import socket
from cryptography import fernet
import rsa
import json
import os
from exceptions import ConnectionFailedError, InvalidPackageException
import re
import random

PATH = os.path.dirname(os.path.realpath(__file__))
class Client:
    def __init__(self, addr):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connect_to_server(addr)
        except:
            raise ConnectionFailedError

    def connect_to_server(self, addr):
        self.client_socket.connect(addr)
        
        data = self.client_socket.recv(256)
        print('Received data from server')
        signature = self.client_socket.recv(128)
        print('Received signature from server')

        rsa_key_public = rsa.PublicKey.load_pkcs1(data)
        print('Loading rsa key...')
        correct = rsa.verify(data, signature, rsa_key_public)
        print('Verifying...')
        if not correct:
            raise Exception('rsa verification failed')
        print('rsa verification passed')

        symmetric_key = fernet.Fernet.generate_key()
        self.endec = fernet.Fernet(symmetric_key)
        self.client_socket.send(rsa.encrypt(symmetric_key, rsa_key_public))
        print('Sent symmetric key to server')

    def send_package(self, package: dict):
        json_dump = json.dumps(package)
        encrypted = self.endec.encrypt(json_dump.encode())
        self.client_socket.send(encrypted)
        print(f'sent "{package["type"]}" package')

    def recieve_package(self, expected_type: str):
        header = self.client_socket.recv(1024)
        header_package = json.loads(self.endec.decrypt(header).decode())
        response = self.client_socket.recv(header_package['size-of-package'])
        response_package = json.loads(self.endec.decrypt(response).decode())

        print(header_package)
        print(response_package)
        
        if response_package['type'] != expected_type:
            print('Invalid response received')
            raise InvalidPackageException
        
        return response_package

    def send_login_request(self, username: str, password: str):
        is_valid = self.validate_credentials(username, password)
        if not is_valid[0]:
            return (False, is_valid[1])
        
        package = {
            "type": "login",
            "username": username,
            "password-hash": password
        }
        self.send_package(package)

        try:
            response_package = self.recieve_package('login_response')
        except InvalidPackageException:
            return (False, 'Invalid Package')
        print('responded to "login" package')

        return (response_package['allowed'], response_package['response'])

    def send_signup_request(self, username: str, password: str):
        is_valid = self.validate_credentials(username, password)
        if not is_valid[0]:
            return (False, is_valid[1])
        
        package = {
            "type": "signup",
            "username": username,
            "password-hash": password
        }
        self.send_package(package)
        
        try:
            response_package = self.recieve_package('signup_response')
        except InvalidPackageException:
            return (False, 'Invalid Package')
        print('responded to "signup" package')

        if response_package['allowed']:
            return (True, 'signup successful')
        else:
            return (False, response_package['response'])
    
    def validate_credentials(self, username: str, password: str) -> tuple[bool, str]:
        if not username:
            return (False, 'username cannot be empty')
        
        if len(username) > 16:
            return (False, 'username must be 16 characters or less')
        
        if not re.match(r'^[a-z0-9]+$', username):
            return (False, 'username can only contain lowercase letters and numbers')
        
        if not password:
            return (False, 'password cannot be empty')
        
        return (True, '')
        
    def notify_logout(self):
        package = {
            "type": "logout"
        }
        self.send_package(package)
        try:
            response_package = self.recieve_package('logout_acknowledged')
        except InvalidPackageException:
            return False
        print('responded to "logout" package')
        
        return True

    def send_upload_request(self, file_path: str, is_public: bool):
        if not os.path.isfile(file_path):
            return (False, 'File doesnt exist')
        
        file_size = os.path.getsize(file_path)
        package = {
            "type": "upload_request",
            "file-data": {
                "file-name": file_path.rsplit('\\')[-1],
                "file-size-bytes": file_size,
                "is-public": is_public
            }
        }                
        self.send_package(package)

        try:
            response_package = self.recieve_package('upload_request_response')
        except InvalidPackageException:
            return (False, 'Invalid Package')
        print('responded to "upload_request" package')
        
        return (response_package['allowed'], response_package['response'])
    
    def upload_file(self, file_path: str):
        with open(file_path, 'rb') as f:
            file_data = f.read()

        encrypted = self.endec.encrypt(file_data)
        
        header_package = {
            "type": "upload_start",
            "encrypted-size": len(encrypted)
        }
        self.send_package(header_package)
        
        self.client_socket.sendall(encrypted)

        try:
            response_package = self.recieve_package('upload_final')
        except InvalidPackageException:
            return (False, None)
        print('responded to "upload"')
        return (response_package['completed'], response_package['file-data'])
    
    def send_download_request(self, username: str, file_name: str):
        request_package = {
            "type": "download_request",
            "username": username,
            "file-name": file_name
        }
        self.send_package(request_package)

        try:
            response_package = self.recieve_package('download_request_response')
        except InvalidPackageException:
            return (False, 'Invalid Package')
        print('responded to "download_request" package')

        return (response_package['allowed'], response_package['response'])
    
    def download_file(self, file_name: str):
        header_package = self.recieve_package('download_start')
        data = self.client_socket.recv(header_package['encrypted-size'])

        try:
            file = self.endec.decrypt(data)
        except fernet.InvalidToken:
            file_received = False
        else:
            file_received = True

        final_package = {
            "type": "download_final",
            "received": file_received
        }
        self.send_package(final_package)

        if not file_received:
            return False

        base_name, extension = os.path.splitext(file_name)
        self.save_file(base_name, extension, file)
        
        return True
    
    def save_file(self, file_name: str, file_extension: str, file_data: bytes):
        path = PATH + '\\downloads'
        file_path = os.path.join(path, f'{file_name}{file_extension}')
        if os.path.exists(file_path):
            i = 1
            new_file_name = f'{file_name}({i}){file_extension}'
            while os.path.exists(os.path.join(path, new_file_name)):
                i += 1
                new_file_name = f'{file_name}({i}){file_extension}'
            file_path = os.path.join(path, new_file_name)

        with open(file_path, 'wb') as f:
            f.write(file_data)
        
    def change_file_publicity(self, file_name: str):
        package = {
            "type": "file_publicity_change",
            "file-name": file_name
        }
        self.send_package(package)

        try:
            response_package = self.recieve_package('publicity_changed_acknowleged')
        except InvalidPackageException:
            return False
        print('responded to "file_publicity_change" package')

        return True
    
    def delete_file(self, file_name: str):
        package = {
            "type": "delete_file",
            "file-name": file_name
        }
        self.send_package(package)

        try:
            response_package = self.recieve_package('file_deletion_acknowleged')
        except InvalidPackageException:
            return False
        print('responded to "delete_file" package')

        return True
        
    def search_users(self, search_key: str):
        package = {
            "type": "search_users",
            "search-key": search_key
        }
        self.send_package(package)

        try:
            response_package = self.recieve_package('users_found')
        except InvalidPackageException:
            return (False, 'Invalid Package')
        
        #TODO: implement True return and chance False return if necessary
        return (True, response_package['users'])
    
    def get_user_files(self, username: str):
        package = {
            "type": "get_user_files",
            "username": username
        }
        self.send_package(package)

        try:
            response_package = self.recieve_package('user_files')
        except InvalidPackageException:
            return (False, [])
        
        return (True, response_package['files'])