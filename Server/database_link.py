import sqlite3
import os
from exceptions import *

PATH = os.path.dirname(os.path.realpath(__file__))
class DatabaseLink:
    def __init__(self, db_name: str, create: bool = True) -> None:
        '''
        Link to a .db file

        Args:
            db_name [str]: Name of database file (expects it in ./data/)
            create [bool = True]: Try to auto create tables (if not exists)
        
        Returns:
            None
        '''
        if not os.path.exists(PATH + f'\\data\\{db_name}'):
            open(PATH + f'\\data\\{db_name}', 'w') #create file if not exists

        self.connection = sqlite3.connect(f'{PATH}\\data\\{db_name}')
        self.connection.row_factory = sqlite3.Row
        print('Connected to DB')

        self.cursor = self.connection.cursor()
        if create:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            "username" TEXT PRIMARY KEY,
                            "password-hash" TEXT
                            )''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                            "file-name" TEXT,
                            "uploader" TEXT,
                            "file-size-bytes" INTEGER,
                            "upload-time" INTEGER,
                            "is-public" BOOLEAN,
                            "download-count" INTEGER,
                            FOREIGN KEY ("uploader") REFERENCES users("username")
                            PRIMARY KEY ("file-name", "uploader")
                            )''')
            self.connection.commit()

    def add_user(self, username: str, password_hash: str) -> None:
        '''
        Adds a user to the database

        Args:
            username [str]: Username for the user
            password_hash [str]: Password hash of the user

        Returns:
            None

        Raises:
            UserExistsError: if a user with same username already exists (usernames are unique)
        '''

        try:
            self.cursor.execute('INSERT INTO users ("username", "password-hash") VALUES (?, ?)',
                                (username, password_hash))
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise UserExistsError
        
    def get_user(self, username: str) -> dict:
        '''
        Get a user by its username
        
        Args:
            username [str]: Username to get user by

        Returns:
            [dict]: Dictionary containing the users's data as values (keys are the respective column names for each value)
        
        Raises:
            UserNotFoundError: If a user with given username couldn't be found
        
        '''
        self.cursor.execute('SELECT * FROM users WHERE "username"=?',
                            (username,))
        user_data = self.cursor.fetchone()
        if not user_data:
            raise UserNotFoundError

        return dict(user_data)
    
    def get_all_matching_users(self, search_key: str, exclude_non_start: bool=False) -> list[str]:
        '''
        Returns all usernames that start with the given search key, will also return all users who contain the search key if "exclude_non_start" is set to False

        Args:
            search_key [str]: Search key to search by\n
            exclude_non_start [bool = False]: Exclude usernames who dont start with the search key

        Returns:
            [list[str]]: List of usernames matching the search key
        '''
        self.cursor.execute('SELECT "username" FROM users WHERE "username" LIKE ? ORDER BY "username"',
                            (search_key + '%',))
        starts_with_rows = self.cursor.fetchall()
        starts_with_usernames = [dict(row)['username'] for row in starts_with_rows]

        if not exclude_non_start:
            self.cursor.execute('SELECT "username" FROM users WHERE "username" LIKE ? AND "username" NOT LIKE ? ORDER BY "username"',
                                ('%' + search_key + '%', search_key + '%'))
            contains_rows = self.cursor.fetchall()
            contains_usernames = [dict(row)['username'] for row in contains_rows]
        else:
            contains_usernames = []
        
        return starts_with_usernames + contains_usernames
    
    def add_file(self, file_data: dict) -> None:
        '''
        Adds a file to the database

        Args:
            file_data [dict]: File data as a dictionary, expected keys are: 'file-name', 'uploader', 'file-size-bytes', 'upload-time', 'is-public'

        Returns:
            None

        Raises:
            FileExistsError: If a file with the same name (file-name) AND from the same user (uploader) already exists in the database\n
            ValueError: If one (or more) of the expected dictionary keys are missing
        '''
        try:
            self.cursor.execute('INSERT INTO files ("file-name", "uploader", "file-size-bytes", "upload-time", "is-public", "download-count") VALUES (?, ?, ?, ?, ?, ?)',
                                (file_data['file-name'], file_data['uploader'], file_data['file-size-bytes'], file_data['upload-time'], file_data['is-public'], 0))
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise FileExistsError
        except KeyError:
            raise ValueError("Missing dictionary keys. Expected keys are: file-name, uploader, file-size-bytes, upload-time, is-public")
        
    def get_file(self, file_name: str, username: str) -> dict | None:
        '''
        Get a file by its name and uploader's username
        
        Args:
            file_name [str]: File name to search for
            username [str]: Username of the file's uploader

        Returns:
            [dict]: Dictionary containing the users's data as values (keys are the respective column names for each value)
        
        Raises:
            FileNotFoundError: If a file with the given file name from the given uploader couldn't be found
        '''
        self.cursor.execute('SELECT * FROM files WHERE "file-name"=? AND uploader=?',
                            (file_name, username))
        filedata = self.cursor.fetchone()
        if not filedata:
            print('holup')
            raise FileNotFoundError
        
        return dict(filedata)
    
    def delete_file(self, file_name: str, username: str) -> None:
        '''
        Delete a file by its name and uploader's username. Will stop silently if file isn't found
        
        Args:
            file_name [str]: File name to delete
            username [str]: Username of the file's uploader

        Returns:
            None
        '''
        self.cursor.execute('DELETE FROM files WHERE "file-name"=? AND uploader=?',
                            (file_name, username))
        self.connection.commit()

    def remove_user(self, username: str) -> None:
        '''
        Remove a user by its username, will also remove all user's files. Will stop silently if user isn't found
        
        Args:
            file_name [str]: File name to delete
            username [str]: Username of the file's uploader

        Returns:
            None
        '''
        self.cursor.execute('DELETE FROM users WHERE "username"=?',
                            (username,))
        self.cursor.execute('DELETE FROM files WHERE "uploader"=?',
                            (username,))
        self.connection.commit()

    def add_downloads_to_file(self, file_name: str, username: str, count: int=1) -> None:
        '''
        Increases the download count of a given file by a specified amount. Will stop silently if file isn't found

        Args:
            file_name [str]: File name to modify
            username [str]: Username of the file's uploader
            count [int = 1]: Amount to increase by

        Returns:
            None
        '''
        self.cursor.execute('UPDATE files SET "download-count" = "download-count" + ? WHERE "file-name"=? AND "uploader"=?',
                            (count, file_name, username))
        self.connection.commit()

    def change_file_publicity(self, file_name: str, username: str, new_status: bool | None = None) -> None:
        '''
        Changes the publicity status (is_public) of a file. Will stop silently if file isn't found

        Args:
            file_name [str]: File name to modify
            username [str]: Username of the file's uploader
            new_status [bool | None = None] New status (will oppose current if set to None)

        Returns:
            None
        '''
        if new_status is None:
            try:
                f = self.get_file(file_name, username)
                new_status = not f['is-public']
            except FileNotFoundError:
                return
            
        self.cursor.execute('UPDATE files SET "is-public" = ? WHERE "file-name"=? AND "uploader"=?',
                            (new_status, file_name, username))
        self.connection.commit()

    def get_all_user_files(self, username: str, exclude_private: bool = False) -> list[dict]:
        '''
        Get all files belonging to a user by its username. Will return an empty list if user isn't found
        
        Args:
            username [str]: Username of the target user
            exclude_private [bool = False]: Exclude files which are set to private

        Returns:
            [list[dict]]: A list containing the users's file-data as dictionaries
        '''
        if exclude_private:
            self.cursor.execute('SELECT * FROM files WHERE "uploader"=? AND "is-public"=1',
                                (username,))
        else:
            self.cursor.execute('SELECT * FROM files WHERE "uploader"=?',
                                (username,))
            
        filedata = self.cursor.fetchall()
        files = [dict(row) for row in filedata]

        return files
    
    def count_public_files(self, username: str) -> int:
        '''
        Count all public files belonging to a user by its username. Will return 0 if user isn't found

        Args:
            username [str]: Username of the target user

        Returns:
            [int]: Number of public files belonging to the user
        '''
        self.cursor.execute('SELECT COUNT(*) FROM files WHERE "uploader"=? AND "is-public"=1',
                            (username,))
        
        return dict(self.cursor.fetchone())['COUNT(*)']
    
    def close(self) -> None:
        '''
        Closes connection with db

        Returns:
            None
        '''
        self.connection.close()


        
def main():
    d = DatabaseLink('database.db')
    d.cursor.execute('SELECT * FROM files')
    l = d.cursor.fetchall()
    print([dict(e) for e in l])
    d.cursor.execute('SELECT COUNT(*) FROM files')
    l = d.cursor.fetchone()
    print(dict(l)['COUNT(*)'])
    

if __name__ == '__main__':
    print('main db')
    main()