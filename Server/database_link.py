import sqlite3
import os
from exceptions import *

PATH = os.path.dirname(os.path.realpath(__file__))
class DataBaseLink:
    def __init__(self, db_name: str) -> None:
        '''
        link to a .db file and store users and filedata

        PARAMATERS:
        db_name: str -> name of .db file

        RETURNS: None
        '''
        self.connection = sqlite3.connect(f'{PATH}\\data\\{db_name}')

        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password_hash TEXT
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                            file_name TEXT,
                            uploader TEXT,
                            file_size_bytes INTEGER,
                            upload_time INTEGER,
                            is_public BOOLEAN,
                            download_count INTEGER,
                            FOREIGN KEY (uploader) REFERENCES users(username)
                            PRIMARY KEY (file_name, uploader)
                            )''')
        self.connection.commit()

    def add_user(self, username: str, password_hash: str) -> None:
        '''
        add a user to the database
        raises UserExistsError if exists a user with the same username

        PARAMATERS: 
        username: str -> the user's username
        password_hash: str -> the user's hashed password

        RETURNS: None
        '''
        try:
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                                (username, password_hash))
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise UserExistsError
        
    def get_user(self, username: str) -> dict:
        '''
        returns a user from the database
        raises UserNotFoundError if username is not found

        PARAMATERS: 
        username: str -> username to search for

        RETURNS: dict -> the user requested in the form of a dictionary with "username" & "password-hash" as keys
        '''        
        self.cursor.execute("SELECT * FROM users WHERE username=?",
                            (username,))
        user_data = self.cursor.fetchone()
        if not user_data:
            raise UserNotFoundError
        
        return {
            "username": user_data[0],
            "password-hash": user_data[1]
        }
    
    def get_all_matching_users(self, search_key: str, exclude_non_start: bool=False) -> list[str]:
        '''
        returns all usernames that start with the given search_key, will also return all users who contain the search_key anywhere if "exclude_non_start" is set to False,
        will sort all the users who start with search-key alphabetically and will add all those who contain in not in the start (also sorted alphabetically)

        PARAMATERS:
        search_key: str -> key to search by
        exclude_non_start: bool (default=False) -> include usernames who contain the start key anywhere in their names

        RETURNS: list[str] -> all usernames containing the search key (according to the sorting mentioned previously)
        '''        
        self.cursor.execute("SELECT username FROM users WHERE username LIKE ? ORDER BY username",
                            (search_key + '%',))
        starts_with_rows = self.cursor.fetchall()
        starts_with_usernames = [row[0] for row in starts_with_rows]

        if not exclude_non_start:
            self.cursor.execute("SELECT username FROM users WHERE username LIKE ? AND username NOT LIKE ? ORDER BY username", 
                                ('%' + search_key + '%', search_key + '%'))
            contains_rows = self.cursor.fetchall()
            contains_usernames = [row[0] for row in contains_rows]
        else:
            contains_usernames = []

        return starts_with_usernames + contains_usernames
    
    def add_file(self, file_data: dict) -> None:
        '''
        adds a file to the database
        raises DuplicateFileError if a file with the same name AND from the same uploder already exists

        PARAMATERS:
        file_data: dict (expected keys: ['file-name', 'uploader', 'file-size-bytes', 'upload-time', 'is-public']) -> data of file to add

        RETURNS: None
        '''
        try:
            self.cursor.execute("INSERT INTO files (file_name, uploader, file_size_bytes, upload_time, is_public, download_count) VALUES (?, ?, ?, ?, ?, ?)", 
                                (file_data['file-name'], file_data['uploader'], file_data['file-size-bytes'], file_data['upload-time'], file_data['is-public'], 0))
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise DuplicateFileError
        
    def get_file(self, file_name: str, username: str) -> dict | None:
        '''
        returns a file's data from the database

        PARAMATERS:
        file_name: str -> name of file to search
        username: str -> username of file's uploader

        RETURNS: dict | None -> returns a dictionary of the file's data if file was found
                                returns None if no file matched the paramaters
        '''
        self.cursor.execute("SELECT * FROM files WHERE file_name=? AND uploader=?",
                            (file_name, username))
        
        filedata = self.cursor.fetchone()
        if not filedata:
            return None
        
        return {
            "file-name": filedata[0],
            "file-size-bytes": filedata[2],
            "upload-time": filedata[3],
            "is-public": bool(filedata[4]),
            "download-count": filedata[5]
        }
        
    def delete_file(self, file_name: str, username: str) -> None:
        '''
        deletes a file from the database
        ignores if file doesn't exist

        PARAMATERS:
        file_name: str -> name of file to delete
        username: str -> username of file's uploader

        RETURNS: None
        '''
        self.cursor.execute("DELETE FROM files WHERE file_name=? AND uploader=?",
                            (file_name, username))
        self.connection.commit()
    
    def remove_user(self, username: str) -> None:
        '''
        removes a user and all its files from the database
        ignores if user doesn't exist
        
        PARAMATERS:
        username: str -> username to delete

        RETURNS: None
        '''
        self.cursor.execute("DELETE FROM users WHERE username=?",
                            (username,))
        self.cursor.execute("DELETE FROM files WHERE uploader=?",
                            (username,))
        self.connection.commit()

    def add_downloads_to_file(self, file_name: str, username: str, count=1) -> None:
        '''
        modifies the download_count of a given file by the specified amount

        PARAMATERS:
        file_name: str -> name of file to modify
        username: str -> username of file's uploader
        count: int (default=1) -> amount to modify by

        RETURNS: None
        '''
        self.cursor.execute("UPDATE files SET download_count = download_count + ? WHERE file_name=? AND uploader=?",
                            (count, file_name, username))
        self.connection.commit()

    def change_file_publicity(self, file_name: str, username: str, new_status: bool | None=None) -> None:
        '''
        changes the publicity status of a file, will change to the opposite of what's current if no "new_status" is provided,
        else will change to provided "new_status"

        PARAMATERS:
        file_name: str -> name of file to modify
        username: str -> username of file's uploader
        new_status: bool | None (default=None) -> the status to set (will oppose current if None)

        RETURNS: None
        '''
        if new_status is None:
            f = self.get_file(file_name, username)
            new_status = not f['is-public']

        self.cursor.execute("UPDATE files SET is_public = ? WHERE file_name=? AND uploader=?",
                            (new_status, file_name, username))
        self.connection.commit()

    def get_all_user_files(self, username: str, exclude_private: bool=False) -> list[dict]:
        '''
        returns all files belonging to a certain user

        PARAMATERS:
        username: str -> username to get its files
        exclude_private: bool (default=False) -> whether to exclude files which are set to private

        RETURNS: list[dict] -> a list containing the data on all files belonging to the user
        '''
        if exclude_private:
            self.cursor.execute("SELECT * FROM files WHERE uploader=? AND is_public=1",
                                (username,))
        else:
            self.cursor.execute("SELECT * FROM files WHERE uploader=?",
                                (username,))

        files = self.cursor.fetchall()
        user_files = []
        for file in files:
            user_files.append({
                "file-name": file[0],
                "file-size-bytes": file[2],
                "upload-time": file[3],
                "is-public": bool(file[4]),
                "download-count": file[5]
            })

        return user_files
    
    def count_all_public_flies(self, username: str) -> int:
        self.cursor.execute('SELECT COUNT(*) FROM files WHERE uploader=? AND is_public=1',
                            (username,))
        return self.cursor.fetchone()[0]
    
    def close(self) -> None:
        '''
        closes connection with db

        RETURNS: None
        '''
        self.connection.close()