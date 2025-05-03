import socket
import select
import rsa
from cryptography import fernet

import os
import shutil
import json
import queue
import time
from datetime import datetime
from threading import Thread, Event
import colorama

from exceptions import *
from database_link import DatabaseLink

from package_formatter import PackageFormatter
from package_validator import PackageValidator

PATH = os.path.dirname(os.path.realpath(__file__))
class Server:
    def __init__(self, port: int, db_name: str):
        '''
        Creates the server\n
        Requires files: package_formatter.py, package_validator.py, exceptions.py, database_link.py, and a directory "data" containing RSA encryption keys (in PEM format) in "encryption-keys", a sub-directory "files", and a .db file
    
        Args:
            port [int]: Port to open on
            db_name [str]: Name of .db file

        Returns:
            None
        '''
        colorama.init(autoreset=True)

        self.load_rsa_keys()
        self.db_read = DatabaseLink(db_name)
        self.db_write_queue = queue.Queue()

        self.max_file_size = 25 * 1024 * 1024 #25 MB

        self.handle_map = {
            'login': self.handle_login_request,
            'signup': self.handle_signup_request,
            'logout': self.handle_logout_request,
            'upload_request': self.handle_upload_request,
            'download_request': self.handle_download_request,
            'file_publicity_change': self.handle_file_publicity_change_request,
            'delete_file': self.handle_file_deletion_request,
            'search_users': self.handle_user_search_request,
            'get_user_files': self.handle_user_files_request
        }

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', port))

        self.active_sockets: list[socket.socket] = []
        self.socket_to_user: dict[socket.socket: str] = {}
        self.user_endec_map: dict[socket.socket: fernet.Fernet] = {}
        self.file_transfers: list[socket.socket] = []

        self.close_server_event = Event()
        
        Thread(target=self.admin_input).start()
        Thread(target=self.db_write, args=(db_name,)).start()

    def handle_clients(self, backlog=1):
        '''
        Allow the server to accept clients and handle their request

        Args:
            backlog [int]: Backlog of sockets allowed to be queued for acception

        Returns:
            None
        '''
        self.server_socket.listen(backlog)
        print('Server is listening...')

        while not self.close_server_event.is_set():
            r_list, _, _ = select.select(self.active_sockets + [self.server_socket], [], [], 1)

            for client_soc in r_list:
                if client_soc is self.server_socket:
                    Thread(target=self.connect_new_socket).start()
                    continue

                if client_soc in self.file_transfers:
                    continue

                data = self.read_from_socket(client_soc)
                if not data:
                    self.close_socket(client_soc)
                    continue

                converted, package = self.data_to_package(data, self.user_endec_map[client_soc])
                if not converted:
                    response_package = PackageFormatter.invalid_package(package)
                    self.send_package(client_soc, response_package)
                    continue
                print(f'{colorama.Fore.GREEN}{package}')

                is_valid, invalid_response = PackageValidator.validate_package(package)
                if is_valid:
                    response_package = self.handle_map[package['type']](client_soc, package)
                else:
                    response_package = PackageFormatter.invalid_package(invalid_response)

                print(f'{colorama.Fore.BLUE}{response_package}')
                self.send_package(client_soc, response_package)
        
        self.close_server()

    def handle_login_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a login request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        try:
            user = self.db_read.get_user(package['username'])
        except UserNotFoundError:
            return PackageFormatter.response_package('login_response', False, 'User doesn\'t exist')
        
        if package['password-hash'] != user['password-hash']:
            return PackageFormatter.response_package('login_response', False, 'Incorrect password')
        
        if package['username'] in self.socket_to_user.values():
            return PackageFormatter.response_package('login_response', False, 'User is logged-in from another location')
        
        self.socket_to_user[client_soc] = package['username']
        return PackageFormatter.response_package('login_response', True, self.db_read.get_all_user_files(package['username']))
    
    def handle_signup_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a signup request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        user_folder_path = PATH + f'\\data\\files\\{package['username']}'
        try:
            os.makedirs(user_folder_path)
        except FileExistsError:
            return PackageFormatter.response_package('signup_response', False, 'Username taken')
        
        self.add_to_write_queue('add_user', package['username'], package['password-hash'])
        self.socket_to_user[client_soc] = package['username']
        return PackageFormatter.response_package('signup_response', True)
    
    def handle_logout_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a logout request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        try:
            self.socket_to_user.pop(client_soc)
        except KeyError:
            return PackageFormatter.response_package('logout_response', False, 'User was not connected')
        
        return PackageFormatter.response_package('logout_response', True)
    
    def handle_upload_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a file upload request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        file_data = package['file-data']
        try:
            self.db_read.get_file(file_data['file-name'], self.socket_to_user[client_soc])
        except FileNotFoundError:
            pass
        else:
            #file exists
            return PackageFormatter.response_package('upload_request_response', False, 'File already exists')

        if (file_data['file-size-bytes']) > self.max_file_size:
            return PackageFormatter.response_package('upload_request_response', False, 'File too large')

        Thread(target=self.file_upload, args=(client_soc, file_data)).start()
        return PackageFormatter.response_package('upload_request_response', True)
    
    def file_upload(self, client_soc: socket.socket, file_desc: dict):
        '''
        File upload function, expected to run in a different thread from main server

        Args:
            client_soc [socket.socket]: The user's socket
            file_desc [dict]: Description of file to upload

        Returns:
            None
        '''
        self.file_transfers.append(client_soc)
        print(f'{client_soc.getpeername()[0]} entered file transfer')

        data = self.read_from_socket(client_soc)
        if not data:
            self.close_socket(client_soc)
            return
        
        converted, header_package = self.data_to_package(data, self.user_endec_map[client_soc])
        if not converted:
            response_package = PackageFormatter.invalid_package('Could not convert data to package')
            self.send_package(client_soc, response_package)
            return
        
        keys = ['type', 'encrypted-size']
        if (not all(key in header_package for key in keys)) or (header_package['type'] != 'upload_start'):
            response_package = PackageFormatter.invalid_package('Invalid header package')
            self.send_package(client_soc, response_package)
            return
        
        unix_timestamp = round(datetime.now().timestamp())
        file_desc['upload-time'] = unix_timestamp

        file_encrypted = client_soc.recv(header_package['encrypted-size'])
        try:
            file = self.user_endec_map[client_soc].decrypt(file_encrypted)
        except fernet.InvalidToken:
            completed = False
        else:
            completed = True

        file_data = file_desc.copy() if completed else 'Failed to decrypt file'
        if completed:
            file_data['download-count'] = 0

        finish_package = PackageFormatter.response_package('upload_final', completed, file_data)
        self.send_package(client_soc, finish_package)

        if completed:
            self.add_file_by_username(self.socket_to_user[client_soc], file, file_desc)

        self.file_transfers.remove(client_soc)
        print(f'{client_soc.getpeername()[0]} finished file transfer')

    def handle_download_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a file download request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        file = self.db_read.get_file(package['file-name'], package['username'])
        if (package['username'] != self.socket_to_user[client_soc]) and (not file['is-public']):
            return PackageFormatter.response_package('download_request_response', False, 'No access to file')
        
        Thread(target=self.file_download, args=(client_soc, file, package['username'])).start()
        return PackageFormatter.response_package('download_request_response', True)
    
    def file_download(self, client_soc: socket.socket, file_desc: dict, uploader: str):
        '''
        File download function, expected to run in a different thread from main server

        Args:
            client_soc [socket.socket]: The user's socket
            file_desc [dict]: Description of file to download
            uploader [str]: Username of file's uploader
            
        Returns:
            None
        '''
        #delay to adjust for client time
        time.sleep(1)

        file_name: str = file_desc['file-name']
        user_endec: fernet.Fernet = self.user_endec_map[client_soc]

        file_path = PATH + f'\\data\\files\\{uploader}\\{file_name}'
        with open(file_path, 'rb') as f:
            file_data = f.read()

        encrypted = user_endec.encrypt(file_data)
        header_package = {
            "type": "download_start",
            "encrypted-size": len(encrypted)
        }
        self.send_package(client_soc, header_package)
        client_soc.sendall(encrypted)
        
        confirmation = self.read_from_socket(client_soc)
        converted, confirmation_package = self.data_to_package(confirmation, self.user_endec_map[client_soc])
        if converted and confirmation_package['received']:
            self.add_to_write_queue('add_downloads_to_file', file_name, uploader)

    def handle_file_publicity_change_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a file publicity change request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        username = self.socket_to_user[client_soc]
        try:
            self.db_read.get_file(package['file-name'], username)
        except FileNotFoundError:
            return PackageFormatter.response_package('file_publicity_change_response', False, 'File doesn\'t exist')
        
        self.add_to_write_queue('change_file_publicity', package['file-name'], username)
        return PackageFormatter.response_package('file_publicity_change_response', True)
    
    def handle_file_deletion_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a file deletion request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        username = self.socket_to_user[client_soc]
        try:
            self.db_read.get_file(package['file-name'], username)
        except FileNotFoundError:
            return PackageFormatter.response_package('file_deletion_response', False, 'File doesn\'t exist')
        
        os.remove(PATH + f'\\data\\files\\{username}\\{package['file-name']}')
        self.add_to_write_queue('delete_file', package['file-name'], username)
        return PackageFormatter.response_package('file_deletion_response', True)
    
    def handle_user_search_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a user search request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        username = self.socket_to_user[client_soc]

        matching_users = self.db_read.get_all_matching_users(package['search-key'])
        try:
            #remove request maker from matching users
            matching_users.remove(username)
        except ValueError:
            #user doesnt exist in matching users
            pass

        users = {username: self.db_read.count_public_files(username) for username in matching_users}
        return PackageFormatter.response_package('users_found', True, users)
    
    def handle_user_files_request(self, client_soc: socket.socket, package: dict):
        '''
        Handles a user files request by a user

        Args:
            client_soc [socket.socket]: The user's socket
            package [dict]: Package sent by the user

        Returns:
            [dict]: Response package for the user
        '''
        files = self.db_read.get_all_user_files(package['username'], True)
        for file in files:
            file.pop('is-public')
            file.pop('download-count')

        return PackageFormatter.response_package('user_files', True, files)

    def add_file_by_username(self, username: str, file: bytes, file_desc: dict):
        '''
        Add a file to the database

        Args:
            username [str]: File's uploader's username
            file [bytes]: Actual file in bytes
            file_desc [dict]: Description of file

        Returns:
            None
        '''
        file_path = PATH + f'\\data\\files\\{username}\\{file_desc['file-name']}'
        with open(file_path, 'wb') as f:
            f.write(file)

        file_desc['uploader'] = username
        self.add_to_write_queue('add_file', file_desc)

    def connect_new_socket(self):
        '''
        Allows new socket to connect and go through initial connection process, expected to run in a seperate thread
        
        Returns:
            None
        '''
        client_soc, client_addr = self.server_socket.accept()
        print(f'Connection from {client_addr}')
        try:
            key = self.rsa_key_public.save_pkcs1()
            client_soc.send(key)
            print(f'Public key sent to {client_addr}')

            signature = rsa.sign(key, self.rsa_key_private, 'SHA-1')
            client_soc.send(signature)
            print(f'Signature sent to {client_addr}')

            data = client_soc.recv(1024)
            try:
                symmetric_key = rsa.decrypt(data, self.rsa_key_private)
            except rsa.DecryptionError:
                print(f'Received invalid data from {client_addr}, aborting')
                client_soc.close()
                return
            print(f'Received symmetric key from {client_addr}')

            try:
                client_endec = fernet.Fernet(symmetric_key)
            except ValueError:
                print(f'Received invalid symmetric key from {client_addr}, aborting')
                client_soc.close()
                return
            
            self.active_sockets.append(client_soc)
            self.user_endec_map[client_soc] = client_endec
            print(f'{client_addr}, completed connection!')

        except ConnectionError:
            print(f'{client_addr} disconnected during connection, aborting')
            client_soc.close()

    def read_from_socket(self, client_soc: socket.socket) -> bytes:
        '''
        Reads 2048 bytes from a socket

        Args:
            client_soc [socket.socket]: Socket to read from

        Returns:
            [bytes]: Data read from the socket
        '''
        try:
            data = client_soc.recv(2048)
        except ConnectionError:
            data = b''

        return data

    def data_to_package(self, data: bytes, endec: fernet.Fernet) -> tuple[bool, dict | str]:
        '''
        Convert bytes to a formatted package

        Args:
            data [bytes]: Data to convert
            endec [fernet.Fernet]: User's Fernet endec

        Returns:
            [tuple[bool, dict | str]]: Tuple containing 2 elements, first indicating whether the package was converted successfully, second will be the package as a dict (if converted successfully) else an error message (str)
        '''
        try:
            package = json.loads(endec.decrypt(data))
        except fernet.InvalidToken:
            return (False, 'Failed to decrypt data')
        except UnicodeDecodeError:
            return (False, 'Failed to decode data')
        except json.JSONDecodeError:
            return (False, 'Failed to format as json')

        return (True, package)
    
    def send_package(self, client_soc: socket.socket, package: dict) -> None:
        '''
        Sends a package to a socket, assumes socket completed connection through connect_new_socket(). Encrypts the package using the socket's mapped endec, and sends a header package containing size of packge (in bytes) first.

        Args:
            client_soc [socket.socket]: Socket to send package to
            package [dict]: Packge to send

        Returns:
            None
        '''
        encrypted = self.encrypt(self.user_endec_map[client_soc], package)

        header = {
            "type": "header_package",
            "size-of-package": len(encrypted)
        }
        encrypted_header = self.encrypt(self.user_endec_map[client_soc], header)

        client_soc.send(encrypted_header)
        client_soc.sendall(encrypted)

    def encrypt(self, endec: fernet.Fernet, package: dict) -> bytes:
        '''
        Encrypts a package using a socket's mapped endec

        Args:
            endec [fernet.Fernet]: Fernet object to encrypt through
            package [dict]: Package to encrypt

        Returns:
            [bytes]: package as encrypted bytes
        '''
        data = json.dumps(package).encode()
        return endec.encrypt(data)
    
    def close_socket(self, client_soc: socket.socket):
        '''
        Closes connection with a socket, and removes it from any internal variables that might store it

        Args:
            client_soc [socket.socket]: Socket to close

        Returns:
            None
        '''
        addr = client_soc.getpeername()[0]

        self.active_sockets.remove(client_soc)
        self.user_endec_map.pop(client_soc)
        try:
            self.socket_to_user.pop(client_soc)
        except KeyError:
            pass

        client_soc.close()
        print(f'Closed connection with {addr}')

    def add_to_write_queue(self, request: str, *args) -> None:
        '''
        Add a db write request to the write queue

        Args:
            request [str]: The request to make
            *args: all arguments needed for that request type

        Returns:
            None
        '''
        self.db_write_queue.put((request, (*args,)))
        self.db_queue_not_empty.set()

    def db_write(self, db_name: str):
        '''
        Creates a connection to the DB and reads request through "db_write_queue", should only be used for write requests as nothing will be returned

        Args:
            db_name [str]: Name of .db file

        Returns:
            None
        '''
        write_db = DatabaseLink(db_name, False)
        self.db_queue_not_empty = Event()
        function_map = {
            "add_user": write_db.add_user,
            "add_file": write_db.add_file,

            "remove_user": write_db.remove_user,
            "delete_file": write_db.delete_file,

            "add_downloads_to_file": write_db.add_downloads_to_file,
            "change_file_publicity": write_db.change_file_publicity,
        }

        while not self.close_server_event.is_set():
            while not self.db_write_queue.empty():
                r = self.db_write_queue.get()
                function_map[r[0]](*r[1])
            
            self.db_queue_not_empty.clear()
            self.db_queue_not_empty.wait()

        write_db.close()

    def admin_input(self) -> None:
        '''
        allows input on the server program to enter basic commands

        command list:\n
        -stop -> will stop the server\n
        -sockets -> print all currently connected sockets\n
        -logged in -> show all sockets mapped to a user and which user they are mapped to\n
        -removeuser {username} -> will completely remove a user and all its files (UNREVERSABLE)

        Returns:
            None
        '''
        while not self.close_server_event.is_set():
            command = input()
            if command == 'stop':
                self.close_server_event.set()

            elif command == 'sockets':
                print(self.active_sockets)

            elif command == 'logged_in':
                print(self.socket_to_user)

            elif command.startswith('removeuser '):
                if len(command) == len('removeuser '):
                    print(f'username cannot be empty')
                    continue
                self.remove_user(command[len('removeuser '):])

            else:
                print('unrecognized command')

    def remove_user(self, username: str) -> None:
        '''
        Removes a user and all its files

        Args:
            username [str]: Username of target user

        Returns:
            None
        '''
        self.add_to_write_queue('remove_user', username)
        shutil.rmtree(PATH + '\\data\\files\\' + username)
        print(f'Removed user {username}')

    def load_rsa_keys(self):
        '''
        Loads the RSA keys from ./data/encryption_keys and stores them
        assumes file tree is valid

        Returns:
            None
        '''
        with open(PATH + '\\data\\encryption_keys\\publickey.pem', 'rb') as f:
            self.rsa_key_public = rsa.PublicKey.load_pkcs1(f.read())
        with open(PATH + '\\data\\encryption_keys\\privatekey.pem', 'rb') as f:
            self.rsa_key_private = rsa.PrivateKey.load_pkcs1(f.read())

        print('Loaded RSA keys.')

    def close_server(self):
        '''
        Closes the server and disconnects all sockets

        Returns:
            None
        '''
        for client_soc in self.active_sockets:
            self.close_socket(client_soc)

        self.db_read.close()
        self.db_queue_not_empty.set()

def main():
    s = Server(11111, 'database.db')
    s.handle_clients()

if __name__ == '__main__':
    main()