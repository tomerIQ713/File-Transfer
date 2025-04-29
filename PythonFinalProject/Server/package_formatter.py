class PackageFormatter:
    @staticmethod
    def invalid_package(response: str=''):
        '''
        default response to any package that couldn't be handled by the server
        
        PARAMATERS:
        response: str -> a response message explaining why the package is invalid

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "invalid_package",
            "response": response
        }
    
    @staticmethod
    def login_response(allowed: bool, response: list | str):
        '''
        response to a login request sent by a user

        PARAMATERS:
        allowed: bool -> whether the request has been allowed or denied
        respone: list | str -> expects a list containing the user's files if allowed is true, 
                               expects a denial reason (str) incase allowed is false

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "login_response",
            "allowed": allowed,
            "response": response
        }

    @staticmethod
    def signup_response(allowed: bool, response: str=''):
        '''
        response to a signup request sent by a user

        PARAMATERS:
        allowed: bool -> whether the request has been allowed or denied
        response: str (default='') -> a reason for allowence / denial

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "signup_response",
            "allowed": allowed,
            "response": response
        }
    
    @staticmethod
    def acknowledge_logout():
        '''
        response to a logout package sent by a user
        
        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "logout_acknowledged"
        }
    
    @staticmethod
    def file_upload_response(allowed: bool, response: str=''):
        '''
        response to a file_upload request sent by a user

        PARAMTERS:
        allowed: bool -> whether the request has been allowed or denied
        response: str (default='') -> a reason for refusal

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "upload_request_response",
            "allowed": allowed,
            "response": response
        }
    
    @staticmethod
    def file_upload_final(completed: bool, file_data: dict | None = None):
        '''
        final upload status sent after an upload

        PARAMTERS:
        completed: bool -> whether the upload has been completed successfully
        response: dict | None (default=None) -> file data of new file if completed successfully else None

        RETURNS: dict -> the package to send to the user
        '''        
        return {
            "type": "upload_final",
            "completed": completed,
            "file-data": file_data
        }
    
    @staticmethod
    def file_download_response(allowed: bool, response: str=''):
        '''
        response to a file_download request sent by a user

        PARAMTERS:
        allowed: bool -> whether the request has been allowed or denied
        response: str (default='') -> a reason for refusal

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "download_request_response",
            "allowed": allowed,
            "response": response
        }        
    
    @staticmethod
    def acknowledge_file_publicity_change():
        '''
        response to a change_file_publicity package sent by a user

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "publicity_changed_acknowleged"
        }    
    
    @staticmethod
    def acknowledge_file_deletion():
        '''
        response to a file_delete package sent by a user

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "file_deletion_acknowleged"
        }
    
    @staticmethod
    def users_found(users: dict):
        '''
        response to a search_users request sent by a user

        PARAMATERS:
        users: dict -> {username: file_count} for all matching users

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "users_found",
            "users": users
        }
    
    @staticmethod
    def user_files(files: list[dict]):
        '''
        response to a get_user_files request sent by a user

        PARAMATERS:
        files: list[dict] -> a list of all matching files

        RETURNS: dict -> the package to send to the user
        '''
        return {
            "type": "user_files",
            "files": files
        }