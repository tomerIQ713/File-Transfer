import socket
import rsa
from cryptography import fernet

import os
import json
import re
import hashlib

from typing import Any
from exceptions import *

PATH = os.path.dirname(os.path.realpath(__file__))
class Client:
    def __init__(self, addr):
        '''
        Creates a client socket to communicate with the server and manage package formatting

        Args:
            addr: Server's address

        Returns:
            None
        '''
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server(addr)

    def send_login_package(self, username: str, password: str) -> tuple[bool, list | str]:
        '''
        Send a login request to the server

        Args:
            username [str]: Username of user
            password [str]: Password of user (will be hashed before sending)

        Returns:
            [tuple[bool, list | str]]: Tuple containing 2 elements, first indicating whether the login was successful or not, second will be a list containing user's files as dictionaries if connected successfully, else will be a rejection string
        '''
        validation = self.validate_credentials(username, password)
        if not validation[0]:
            return (False, validation[1])

        package = {
            'type': 'login',
            'username': username,
            'password-hash': self.hash_string(password)
        }
        return self.send_and_receive(package, 'login_response')

    def send_signup_package(self, username: str, password: str) -> tuple[bool, str]:
        '''
        Send a signup request to the server

        Args:
            username [str]: Username of user
            password [str]: Password of user (will be hashed before sending)

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the signup was successful or not, second will be a rejection string ("" if successful)
        '''
        validation = self.validate_credentials(username, password)
        if not validation[0]:
            return (False, validation[1])

        package = {
            'type': 'signup',
            'username': username,
            'password-hash': self.hash_string(password)
        }
        return self.send_and_receive(package, 'signup_response')

    def send_logout_package(self):
        '''
        Send a logout request to the server

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the logout was successful or not, second will be a rejection string ("" if successful)
        '''
        package = {
            'type': 'logout'
        }
        return self.send_and_receive(package, 'logout_response')
    
    def send_upload_request(self, file_path: str, is_public: bool) -> tuple[bool, str]:
        '''
        Send an upload request to the server

        Args:
            file_path [str]: Path to the file
            is_public [bool]: Upload as public or private file

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the upload request was approved or not, second will be a rejection string ("" if successful)
        '''
        if not os.path.isfile(file_path):
            return (False, 'File doesn\'t exist')
        
        file_size = os.path.getsize(file_path)
        package = {
            'type': 'upload_request',
            'file-data': {
                'file-name': file_path.rsplit('\\')[-1],
                'file-size-bytes': file_size,
                'is-public': is_public
            }
        }
        return self.send_and_receive(package, 'upload_request_response')
        
    def send_download_request(self, file_name: str, username: str) -> tuple[bool, str]:
        '''
        Send an download request to the server

        Args:
            file_name [str]: Name of file to download
            username [str]: Username of file's uploader

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the download request was approved or not, second will be a rejection string ("" if successful)
        '''
        package = {
            'type': 'download_request',
            'file-name': file_name,
            'username': username
        }
        return self.send_and_receive(package, 'download_request_response')
    
    def send_file_publicity_change_request(self, file_name: str) -> tuple[bool, str]:
        '''
        Send a file publicity change request to the server

        Args:
            file_name [str]: Name of file to change publicity

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the change was successful or not, second will be a rejection string ("" if successful)
        '''
        package = {
            'type': 'file_publicity_change',
            'file-name': file_name
        }
        return self.send_and_receive(package, 'file_publicity_change_response')
    
    def send_file_deletion_request(self, file_name: str) -> tuple[bool, str]:
        '''
        Send a file deletion request to the server

        Args:
            file_name [str]: Name of file to change publicity

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the deletion was successful or not, second will be a rejection string ("" if successful)
        '''
        package = {
            'type': 'delete_file',
            'file-name': file_name
        }
        return self.send_and_receive(package, 'file_deletion_response')
    
    def send_user_search_request(self, search_key: str) -> tuple[bool, dict | str]:
        '''
        Send a user search request to the server

        Args:
            search_key [str]: Key to search by

        Returns:
            [tuple[bool, dict | str]]: Tuple containing 2 elements, first indicating whether the search was approved or not, second will be a dict containing matching users to their file count if connected successfully, else will be a rejection string
        '''
        package = {
            "type": "search_users",
            "search-key": search_key
        }
        return self.send_and_receive(package, 'users_found')
    
    def send_user_files_request(self, username: str)  -> tuple[bool, list | str]:
        '''
        Send a user files request to the server

        Args:
            username [str]: Username of requested user

        Returns:
            [tuple[bool, list | str]]: Tuple containing 2 elements, first indicating whether the request was approved or not, second will be a list containing user's files as dictionaries if connected successfully, else will be a rejection string
        '''
        package = {
            'type': 'get_user_files',
            'username': username
        }
        return self.send_and_receive(package, 'user_files')


    def send_package(self, package: dict):
        '''
        Send a package to the server

        Args:
            package [dict]: Package to send

        Returns:
            None
        '''
        json_dump = json.dumps(package)
        encrypted = self.endec.encrypt(json_dump.encode())
        self.client_socket.send(encrypted)
        print(f'Sent {package['type']} package')

    def upload_file(self, file_path: str):
        '''
        Upload a file to the server

        Args:
            file_path [str]: Path to file to upload

        Returns:
            [tuple[bool, dict | str]]: Tuple containing 2 elements, first indicating whether the upload was completed successfully or not, second will be a dict containing uploaded file's data (as determined by the server) if connected successfully, else will be a rejection string
        '''
        with open(file_path, 'rb') as f:
            file_data = f.read()
        encrypted = self.endec.encrypt(file_data)
        
        header_package = {
            'type': 'upload_start',
            'encrypted-size': len(encrypted)
        }
        self.send_package(header_package)
        self.client_socket.sendall(encrypted)

        try:
            response_package = self.receive_package('upload_final')
        except InvalidPackageException:
            return (False, 'Unexpected response package')
        
        return (response_package['accepted'], response_package['response'])
    
    def download_file(self, file_name: str):
        '''
        Download a file from the server

        Args:
            file_path [str]: Name of file to download

        Returns:
            [bool]: Was the file downloaded successfully
        '''
        header_package = self.receive_package('download_start')
        data = self.client_socket.recv(header_package['encrypted-size'])

        try:
            file = self.endec.decrypt(data)
        except fernet.InvalidToken:
            file_received = False
        else:
            file_received = True

        final_package = {
            'type': 'download_final',
            'received': file_received
        }
        self.send_package(final_package)

        if not file_received:
            return False
        
        base_name, extension = os.path.splitext(file_name)
        self.save_file(base_name, extension, file)
        return True

    def receive_package(self, expected_type: str = '') -> dict:
        '''
        Receive a package from the server

        Args:
            expected_type [str = ""]: Expect a specific type of package ("" will accept any package type)

        Returns:
            [dict]: Package received from server

        Raises:
            InvalidPackageException: If type of package received does not match expected type
        '''
        header = self.client_socket.recv(1024)
        header_package = json.loads(self.endec.decrypt(header).decode())
        response = self.client_socket.recv(header_package['size-of-package'])
        response_package = json.loads(self.endec.decrypt(response).decode())
        print(response_package)

        if (expected_type) and (response_package['type'] != expected_type):
            raise InvalidPackageException
        
        return response_package

    def send_and_receive(self, package: dict, expected_response: str) -> tuple[bool, Any]:
        '''
        Send a package to the server, and return the response as a tuple

        Args:
            package [dict]: Package to send
            expected_response [str]: Expected response type

        Returns:
            [tuple[bool, Any]]: Tuple containing 2 elements, first is whether the request was accepted, second is additional response by the server

        '''
        self.send_package(package)
        try:
            response_package = self.receive_package(expected_response)
        except InvalidPackageException:
            return (False, 'Unexpected response package')
        
        return (response_package['accepted'], response_package['response'])

    def hash_string(self, string: str) -> str:
        '''
        Hash a string in sha256

        Args:
            string [str]: string to hash

        Returns:
            [str]: Hashed string in Hex
        '''
        h = hashlib.new('sha256')
        h.update(string.encode())
        return h.hexdigest()

    def validate_credentials(self, username: str, password: str) -> tuple[bool, str]:
        '''
        Validate username and password before sending to the server (to avoid unnecessary traffic)

        Args:
            username [str]: Usename to validate
            password [str]: Password to validate

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the credentials are valid, second is an invalidation message ("" if valid)
        '''
        if not username:
            return (False, 'username cannot be empty')
        
        if len(username) > 16:
            return (False, 'username must be 16 characters or less')
        
        if not re.match(r'^[a-z0-9]+$', username):
            return (False, 'username can only contain lowercase letters and numbers')
        
        if not password:
            return (False, 'password cannot be empty')
        
        return (True, '')

    def save_file(self, file_name: str, file_extension: str, file_data: bytes):
        '''
        Save a file after downloading from server. Downloaded files go to ./downloads

        Args:
            file_name [str]: Name of downloaded file
            file_extension [str]: Extension of downloaded file
            file_data [bytes]: Actual file data

        Returns:
            None
        '''
        path = PATH + '\\downloads'
        file_path = os.path.join(path, f'{file_name}{file_extension}')
        # add numbers after the file name incase file already exists
        if os.path.exists(file_path):
            i = 1
            new_file_name = f'{file_name}({i}){file_extension}'
            while os.path.exists(os.path.join(path, new_file_name)):
                i += 1
                new_file_name = f'{file_name}({i}){file_extension}'
            file_path = os.path.join(path, new_file_name)

        with open(file_path, 'wb') as f:
            f.write(file_data)

    def connect_to_server(self, addr):
        '''
        Connects the socket to the server following pre-planned connection stages        
        '''
        try:
            self.client_socket.connect(addr)

            data = self.client_socket.recv(256)
            signature = self.client_socket.recv(128)

            rsa_key_public = rsa.PublicKey.load_pkcs1(data)
            verified = rsa.verify(data, signature, rsa_key_public)
            if not verified:
                raise Exception

            symmetric_key = fernet.Fernet.generate_key()
            self.endec = fernet.Fernet(symmetric_key)
            self.client_socket.send(rsa.encrypt(symmetric_key, rsa_key_public))

        except:
            raise ConnectionError
        
def main():
    c = Client(('localhost', 11111))

if __name__ == '__main__':
    main()