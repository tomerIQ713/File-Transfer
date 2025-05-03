from typing import Any

class PackageFormatter:
    @staticmethod
    def invalid_package(response: str='') -> dict:
        '''
        Response to a packge that couldn't be handled by the server

        Args:
            response [str='']: Response message to user

        Returns:
            [dict[str, str]]: Package to send to the user
        '''
        return {
            "type": "invalid_package",
            "response": response
        }
    
    @staticmethod 
    def response_package(response_type: str, accepted: bool, response: Any = "") -> dict:
        '''
        Response to a package after handling

        Args:
            accepted [bool]: Whether the original request was accepted or denied
            response: Any response content (optional, "" by default)

        Returns:
            [dict]: Pacakge to send to the user
        '''
        return {
            "type": response_type,
            "accepted": accepted,
            "response": response
        }
