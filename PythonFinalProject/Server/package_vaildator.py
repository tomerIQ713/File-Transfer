import re

class PackageValidator:
    @staticmethod
    def validate_package(package: dict) -> tuple[bool, str]:
        '''
        validates a package

        package must contain "type" as a key
        package will then be validated in a specified internal validator

        PARAMATERS:
        package: dict -> package to validate

        RETURNS: tuple[bool, str] -> a tuple containing 2 elements
                    0: bool -> whether the package is valid
                    1: str -> a message explaining why the package is invalid (will be '' if package is valid)
        '''
        if 'type' not in package:
            return (False, 'Invalid package')
        
        if package['type'] not in PackageValidator.types:
            return (False, 'Invalid request type')
        
        return PackageValidator.types.get(package['type'])(package)
        
    @staticmethod
    def _validate_login_signup_package(package: dict):
        if list(package.keys()) != ['type', 'username', 'password-hash']:
            return (False, 'Invalid keys')
        
        if not package['username'] or len(package['username']) > 16 or not re.match(r'^[a-z0-9]+$', package['username']):
            return (False, 'Invalid username')
        
        if not package['password-hash']:
            return (False, 'Invalid password hash')
        
        return (True, '')
    
    @staticmethod
    def _validate_logout_package(package: dict):
        if len(package) != 1:
            return (False, 'Invalid keys')
        
        return (True, '')
    
    @staticmethod
    def _validate_upload_request_package(package: dict):
        if list(package.keys()) != ['type', 'file-data']:
            return (False, 'Invalid keys')
        
        if (type(package['file-data']) != dict) or (list(package['file-data'].keys()) != ["file-name", "file-size-bytes", "is-public"]):
            return (False, 'Invalid file data')
        
        return (True, '')
    
    @staticmethod
    def _validate_download_request_package(package: dict):
        if list(package.keys()) != ['type', 'username', 'file-name']:
            return (False, 'Invalid keys')
        
        return (True, '')

    @staticmethod
    def _validate_file_modify_package(package: dict):
        if list(package.keys()) != ['type', 'file-name']:
            return (False, 'Invalid keys')
        
        return (True, '')
    
    @staticmethod
    def _validate_user_search_pacakge(package: dict):
        if list(package.keys()) != ['type', 'search-key']:
            return (False, 'Invalid keys')
        
        if not package['search-key'] or len(package['search-key']) > 16:
            return (False, 'Invalid search key')

        return (True, '')
    
    @staticmethod
    def _validate_get_user_files_package(package: dict):
        if list(package.keys()) != ['type', 'username']:
            return (False, 'Invalid keys')
        
        return (True, '')
        
    types = {
        "login": _validate_login_signup_package,
        "signup": _validate_login_signup_package,
        "logout": _validate_logout_package,
        "upload_request": _validate_upload_request_package,
        "download_request": _validate_download_request_package,
        "file_publicity_change": _validate_file_modify_package,
        "delete_file": _validate_file_modify_package,
        "search_users": _validate_user_search_pacakge,
        "get_user_files": _validate_get_user_files_package
    }