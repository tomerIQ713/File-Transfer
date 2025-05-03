import re
from typing import Callable

class PackageValidator:
    @staticmethod
    def validate_package(package: dict) -> tuple[bool, str]:
        '''
        Validates a package
        
        Args:
            package [dict]: Package to validate

        Returns:
            [tuple[bool, str]]: Tuple containing 2 elements, first indicating whether the package was validated successfully, second is a string explaining why package was invalid ("" for valid packages)
        '''

        if 'type' not in package:
            return (False, 'Missing request type')
        
        if package['type'] not in PackageValidator.types:
            return (False, 'Invalid request type')
        
        func, keys = PackageValidator.types[package['type']]
        if not all(key in package for key in keys):
            return (False, 'Invalid keys')
        
        return func(package)
    
    @staticmethod
    def _validate_login_signup_package(package: dict):        
        if (not package['username']) or (len(package['username']) > 16) or (not re.match(r'^[a-z0-9]+$', package['username'])):
            return (False, 'Invalid username')
        
        if not package['password-hash']:
            return (False, 'Invalid password hash')
        
        return (True, '')
    
    @staticmethod
    def _validate_upload_request_package(package: dict):
        file_data_required = ['file-name', 'file-size-bytes', 'is-public']
        if (type(package['file-data']) != dict) or (not all(key in package['file-data'] for key in file_data_required)):
            return (False, 'Invalid file data')
        
        return (True, '')
    
    @staticmethod
    def _validate_user_search_package(package: dict):
        if (not package['search-key']) or (len(package['search-key']) > 16):
            return (False, 'Invalid search key')
        
        return (True, '')

    #request types that do not require further checks (outside of key-matching), will auto-return True
    types: dict[str, tuple[Callable, list[str]]] = {
        "login": (_validate_login_signup_package, ['type', 'username', 'password-hash']),
        "signup": (_validate_login_signup_package, ['type', 'username', 'password-hash']),
        "logout": (lambda _: (True, ''), ['type']),
        "upload_request": (_validate_upload_request_package, ['type', 'file-data']),
        "download_request": (lambda _: (True, ''), ['type', 'file-name', 'username']),
        "file_publicity_change": (lambda _: (True, ''), ['type', 'file-name']),
        "delete_file": (lambda _: (True, ''), ['type', 'file-name']),
        "search_users": (_validate_user_search_package, ['type', 'search-key']),
        "get_user_files": (lambda _: (True, ''), ['type', 'username'])
    }