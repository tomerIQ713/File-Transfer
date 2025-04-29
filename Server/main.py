import socket
import select
from cryptography import fernet
from threading import Thread, Event
import rsa

import os
import shutil
import json
import queue
from datetime import datetime
import time

from exceptions import *
from database_link import DataBaseLink

from package_formatter import PackageFormatter
from package_vaildator import PackageValidator

PATH = os.path.dirname(os.path.realpath(__file__))

class Server:
    def __init__(self, port: int, db_name: str):
        '''
        creates the server

        requires: 
            package_formatter.py, 
            package_validator.py, 
            exceptions.py, 
            database_link.py
        expects a folder named "data" in the same directory as the server, containing all files in a folder named "files" and the RSA encrpytion keys in a PEM format in a folder called "encryption_keys"

        PARAMATERS:
        port: int -> the port to create the server on
        db_name: name for the database file (ie. 'database.db')

        RETURNS: None
        '''
        self.load_rsa_keys()
        self.db_read = DataBaseLink(db_name)
        self.db_write_queue = queue.Queue()

        self.max_file_size = 262144000 #250MB

        self.handle_map = {
            "login": self.handle_login_request,
            "signup": self.handle_signup_request,
            "logout": self.handle_logout_request,
            "upload_request": self.handle_upload_request,
            "download_request": self.handle_download_request,
            "file_publicity_change": self.handle_file_publicity_change_request,
            "delete_file": self.handle_delete_file_request,
            "search_users": self.handle_user_search_request,
            "get_user_files": self.handle_user_files_request
        }
            
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', port))

        self.active_sockets: list[socket.socket] = []
        self.socket_to_user: dict[socket.socket: str] = {}
        self.user_endec_map: dict[socket.socket: fernet.Fernet] = {}
        self.in_file_transfer: list[socket.socket] = []

        self.close_server_event = Event()
        
        Thread(target=self.admin_input).start()
        Thread(target=self.db_write, args=(db_name,)).start()        

    def handle_clients(self, backlog=1):
        '''
        allow the server to accept clients and handle their requests

        PARAMATERS:
        backlog: int (default=1) -> backlog of sockets allowed to queued for acception
        '''
        self.server_socket.listen(backlog)
        print('Server is listening...')

        while not self.close_server_event.is_set():
            r_list, w_list, x_list = select.select(self.active_sockets + [self.server_socket], [], [], 1)
 
            for current_socket in r_list:
                if current_socket is self.server_socket:
                    Thread(target=self.connect_new_socket).start()
                    continue
                
                if current_socket in self.in_file_transfer:
                    continue

                data = self.read_from_socket(current_socket)
                if not data:
                    self.close_socket(current_socket)
                    continue

                converted, package = self.data_to_package(data, self.user_endec_map[current_socket])
                if not converted:
                    response_package = PackageFormatter.invalid_package('Could not convert data to package')
                    self.send_package(current_socket, response_package)
                    continue
                print(package)

                is_valid, invalid_response = PackageValidator.validate_package(package)
                if not is_valid:
                    response_package = PackageFormatter.invalid_package(invalid_response)
                    self.send_package(current_socket, response_package)
                    continue

                response_package = self.handle_map.get(package['type'])(current_socket, package)
                self.send_package(current_socket, response_package)
        
        self.close_server()

    def read_from_socket(self, client_soc: socket.socket):
        '''
        read 2048 bytes from a socket

        PARAMATERS:
        client_soc: socket.socket -> the socket to read from

        RETURNS: bytes
        '''
        try:
            data = client_soc.recv(2048)
        except ConnectionError:
            data = None

        return data

    def handle_login_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a login request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        try:
            user = self.db_read.get_user(package['username'])
        except UserNotFoundError:
            return PackageFormatter.login_response(False, 'user doesn\'t exist')
        
        if package['password-hash'] != user['password-hash']:
            return PackageFormatter.login_response(False, 'non-matching passwords')
        
        if package['username'] in self.socket_to_user.values():
            return PackageFormatter.login_response(False, 'user already connected')
        
        self.socket_to_user[client_soc] = package['username']
        return PackageFormatter.login_response(True, self.db_read.get_all_user_files(package['username']))

    def handle_signup_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a signup request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        user_folder_path = PATH + f'\\data\\files\\{package['username']}'
        try:       
            os.makedirs(user_folder_path)
        except FileExistsError:
            return PackageFormatter.signup_response(False, 'username already taken')

        self.add_to_write_queue('add_user', package['username'], package['password-hash'])
        return PackageFormatter.signup_response(True)
    
    def handle_logout_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a logout request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        self.socket_to_user.pop(client_soc)

        return PackageFormatter.acknowledge_logout()
    
    def handle_upload_request(self, client_soc: socket.socket, package: dict):
        '''
        handles an upload request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        file_data = package['file-data']
        if self.db_read.get_file(file_data['file-name'], self.socket_to_user[client_soc]):
            return PackageFormatter.file_upload_response(False, 'file already exists')
        
        if file_data['file-size-bytes'] > self.max_file_size:
            return PackageFormatter.file_upload_response(False, 'file is too large')
        
        Thread(target=self.file_upload, args=(client_soc, file_data)).start()
        return PackageFormatter.file_upload_response(True)
    
    def file_upload(self, client_soc: socket.socket, file_desc: dict):
        '''
        recives a file from a user, expcets a "header package" stating the length of file to be sent

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        file_desc: dict -> description of file

        RETURNS: None
        '''
        self.in_file_transfer.append(client_soc)
        print(f'{client_soc.getpeername()[0]} entered file transfer')

        data = self.read_from_socket(client_soc)
        if not data:
            self.close_socket(client_soc)
            return
        
        converted, package = self.data_to_package(data, self.user_endec_map[client_soc])
        if not converted:
            response_package = PackageFormatter.invalid_package('Could not convert data to package')
            self.send_package(client_soc, response_package)
            return
        print(package)

        if list(package.keys()) != ["type", "encrypted-size"] or package["type"] != "upload_start":
            response_package = PackageFormatter.invalid_package("Invalid start Package")
            self.send_package(client_soc, response_package)
            return
        
        unix_timestamp = round(datetime.now().timestamp())
        file_desc['upload-time'] = unix_timestamp
        
        file = client_soc.recv(package['encrypted-size'])

        try:
            file = self.user_endec_map[client_soc].decrypt(file)
        except fernet.InvalidToken:
            completed = False
        else:
            completed = True
            
        if completed:
            file_data = {
                "file-name": file_desc['file-name'],
                "file-size-bytes": file_desc['file-size-bytes'],
                "upload-time": file_desc['upload-time'],
                "is-public": file_desc['is-public'],
                "download-count": 0
            }
        else:
            file_data = None

        finish_package = PackageFormatter.file_upload_final(completed, file_data)
        self.send_package(client_soc, finish_package)

        if completed:
            self.add_file_by_username(self.socket_to_user[client_soc], file, file_desc)

        self.in_file_transfer.remove(client_soc)
        print(f'{client_soc.getpeername()[0]} finished file transfer')

    def handle_download_request(self, client_soc: socket.socket, package: dict):
        '''
        handles an download request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        file = self.db_read.get_file(package['file-name'], package['username'])
        if package['username'] != self.socket_to_user[client_soc] and not file['is-public']:
            return PackageFormatter.file_download_response(False, 'no access to file')
        
        Thread(target=self.file_download, args=(client_soc, file, package['username'])).start()
        return PackageFormatter.file_download_response(True)
    
    def file_download(self, client_soc: socket.socket, file_desc: dict, username: str):
        '''
        sends a file to the user

        PARAMATERS:
        client_soc: socket.socket -> the socket to send the file to
        file_desc: dict -> description of the file to be sent
        username: str -> the username of the user who UPLOADED the file
        
        RETURNS: None
        '''
        time.sleep(1)
        file_name: str = file_desc['file-name']
        user_endec: fernet.Fernet = self.user_endec_map[client_soc]

        file_path = PATH + f'\\data\\files\\{username}\\{file_name}'
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
        try:
            converted, confirmation_package = self.data_to_package(confirmation, user_endec)
        except:
            print('did not receive download confirmation from user, ignoring')
            return
        
        if not converted:
            return
        
        if confirmation_package['received']:
            self.add_to_write_queue('add_downloads_to_file', file_name, username)

    def handle_file_publicity_change_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a file publicity change request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        username = self.socket_to_user[client_soc]
        self.add_to_write_queue('change_file_publicity', package['file-name'], username)

        return PackageFormatter.acknowledge_file_publicity_change()
    
    def handle_delete_file_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a file deletion request by the user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user

        RETURNS: dict -> the response package to send to the user
        '''
        username = self.socket_to_user[client_soc]
        file_name = package['file-name']

        os.remove(PATH + f'\\data\\files\\{username}\\{file_name}')
        self.add_to_write_queue('delete_file', file_name, username)

        return PackageFormatter.acknowledge_file_deletion()
    
    def handle_user_search_request(self, client_soc: socket.socket, package: dict):
        '''
        handles a user search request by a user

        PARAMATERS:
        client_soc: socket.socket -> the user's socket
        package: dict -> the package sent by the user
        '''
        username = self.socket_to_user[client_soc]

        matching_users = self.db_read.get_all_matching_users(package['search-key'])
        try:
            #remove user who made the request incase his name appears in the list of matching users
            matching_users.remove(username)
        except ValueError:
            pass

        users = {username: self.db_read.count_all_public_flies(username) for username in matching_users}
        return PackageFormatter.users_found(users)
    
    def handle_user_files_request(self, client_soc: socket.socket, package: dict):
        files = self.db_read.get_all_user_files(package['username'], True)
        for file in files:
            file.pop("is-public")
            file.pop("download-count")

        return PackageFormatter.user_files(files)

    def add_file_by_username(self, username: str, file: bytes, file_desc: dict):
        '''
        add a file to a user by its username, will put the file in the correct folder and write it to the database

        PARAMATERS:
        username: str -> the user's username
        file: bytes -> the file to add
        file_desc: dict -> information about the file, keys expected: ['file-name', 'uploader', 'file-size-bytes', 'upload-time', 'is-public']
        '''
        file_path = PATH + f'\\data\\files\\{username}\\{file_desc['file-name']}'
        with open(file_path, 'wb') as f:
            f.write(file)

        file_data = {
            'file-name': file_desc['file-name'],
            'uploader': username,
            'file-size-bytes': file_desc['file-size-bytes'],
            'upload-time': file_desc['upload-time'],
            'is-public': file_desc['is-public'],
        }

        self.add_to_write_queue('add_file', file_data)

    def send_package(self, client_soc: socket.socket, package: dict):
        '''
        send a package to a socket

        assumes the socket has completed connection correctly following connect_new_socket()

        PARAMATERS:
        client_soc: socket.socket -> the socket to send the package to
        package: the package to send

        RETURNS: None
        '''
        encrypted = self.encrypt(client_soc, package)

        header = {
            "type": "header_package",
            "size-of-package": len(encrypted)
        }
        encrypted_header = self.encrypt(client_soc, header)
        print(package)
        
        client_soc.send(encrypted_header)
        client_soc.sendall(encrypted)

    def encrypt(self, client_soc: socket.socket, package: dict) -> bytes:
        '''
        converts package to encrypted bytes ready to be sent

        PARAMATERS:
        client_soc: socket.socket -> the socket to which the package will be sent (needed for finding encryption key)
        package: dict -> package to encrypt
        
        RETURNS: bytes
        '''
        endec: fernet.Fernet = self.user_endec_map[client_soc]
        data = json.dumps(package).encode()
        return endec.encrypt(data)

    def connect_new_socket(self):
        '''
        allow a new socket to connect

        RETURNS: None
        '''
        client_soc, client_addr = self.server_socket.accept()
        print(f'Connection from {client_addr}')

        key = self.rsa_key_public.save_pkcs1()
        client_soc.send(key)
        print(f'Sent public key to {client_addr}')

        signature = rsa.sign(key, self.rsa_key_private, 'SHA-1')
        client_soc.send(signature)
        print(f'Sent signature to {client_addr}')

        data = client_soc.recv(1024)
        try:
            symmetric_key = rsa.decrypt(data, self.rsa_key_private)
        except rsa.DecryptionError:
            print(f'Received invalid data from {client_addr} on connection establishment, closing connection')
            client_soc.close()
            return
        print(f'Received symmetric key from {client_addr}')

        try:
            client_endec = fernet.Fernet(symmetric_key)
        except ValueError:
            print(f'Received invalid symmetric key from {client_addr} on connection establishment, closing connection')
            client_soc.close()
            return
        print(f'{client_addr} completed connection')

        self.active_sockets.append(client_soc)
        self.user_endec_map[client_soc] = client_endec

    def data_to_package(self, data: bytes, endec: fernet.Fernet) -> tuple[bool, dict | str]:
        '''
        convert bytes send by a user to a readable package

        PARAMATERS:
        data: bytes -> data to convert
        endec: fernet.Fernet -> the user's Fernet endec

        RETURNS: tuple[bool, dict | str] -> a tuple containing 2 elements
                    0: bool -> whether the data could be converted
                    1: dict | str -> if data was converted, will return the package (dict), else return an error message (str)
        '''
        try:
            package = json.loads(endec.decrypt(data).decode())
        except fernet.InvalidToken:
            return (False, 'Failed to decrypt data')
        except UnicodeDecodeError:
            return (False, 'Failed to decode data')
        except json.JSONDecodeError:
            return (False, 'Failed to format data as json')
        
        return (True, package)
    
    def close_socket(self, client_soc: socket.socket):
        '''
        closes a socket

        PARAMATERS:
        client_soc: socket.socket -> the socket to close

        RETURNS: None
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

    def load_rsa_keys(self):
        '''
        loads the RSA keys from /data/encryption_keys and saves them as variables

        assumes the file tree is valid and the keys are in the correct format

        RETURNS: None
        '''
        with open(PATH + '\\data\\encryption_keys\\pubkey.pem', 'rb') as f:
            self.rsa_key_public = rsa.PublicKey.load_pkcs1(f.read())
        with open(PATH + '\\data\\encryption_keys\\privkey.pem', 'rb') as f:
            self.rsa_key_private = rsa.PrivateKey.load_pkcs1(f.read())

    def add_to_write_queue(self, request: str, *args) -> None:
        '''
        add a db_request to the write queue

        PARAMATERS:
        request: str -> the request to make
        *args -> all arguments to add to the query

        RETURNS: None
        '''
        self.db_write_queue.put((request, (*args,)))
        self.db_queue_not_empty.set()

    def db_write(self, db_name: str):
        '''
        creates a connection to the DB and reads requests through "db_write_queue",
        should be used for write requests only as nothing will be returned

        PARAMATERS:
        db_name: str -> name of db

        RETURNS: None
        '''
        write_db = DataBaseLink(db_name)
        self.db_queue_not_empty = Event()
        function_map = {
            "add_user": write_db.add_user,
            "add_file": write_db.add_file,

            "remove_user": write_db.remove_user,
            "delete_file": write_db.delete_file,

            "add_downloads_to_file": write_db.add_downloads_to_file,
            "change_file_publicity": write_db.change_file_publicity
        }

        while not self.close_server_event.is_set():
            while not self.db_write_queue.empty():
                r = self.db_write_queue.get()
                function_map[r[0]](*r[1])
            self.db_queue_not_empty.clear()
            self.db_queue_not_empty.wait()
        
        
        write_db.close()
    
    def admin_input(self):
        '''
        allows input on the server program to enter basic commands

        command list:\n
        -stop -> will stop the server\n
        -sockets -> print all currently connected sockets\n
        -logged in -> show all sockets mapped to a user and which user they are mapped to\n
        -removeuser {username} -> will completely remove a user and all its files (UNREVERSABLE)

        RETURNS: None
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

    def remove_user(self, username: str):
        '''
        removes a user and all its file (UNREVERSABLE)

        PARAMATERS:
        username: str -> the username of the user to delete

        RETURNS: None
        '''
        self.add_to_write_queue('remove_user', username)
        shutil.rmtree(PATH + '\\data\\files\\' + username)
        print(f'removed user {username}')

    def close_server(self):
        '''
        closes the server

        RETURNS: None
        '''
        for client_soc in self.active_sockets:
            self.close_socket(client_soc)
        self.db_read.close()
        self.db_queue_not_empty.set()

def main():
    s = Server(17293, 'database.db')
    s.handle_clients()

if __name__ == '__main__':
    main()