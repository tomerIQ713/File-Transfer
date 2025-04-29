from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image

from client import Client
from exceptions import ConnectionFailedError
from utils import colors, path

#import frames
from frames.connection_failed_frame import ConnectionFailedFrame
from frames.login_page import LoginPage
from frames.main_page import MainPage

DEFAULT_TITLE = 'Project by Ron Katz & Tomer Mazurov'

class GUI(CTk):
    def __init__(self, addr, *args, **kwargs):
        CTk.__init__(self, fg_color=colors['gray_14'], *args, **kwargs)
        connected = self.connect_to_server(addr)
        self.userfiles = []
        
        self.title(DEFAULT_TITLE)
        self.geometry('700x720')
        self.resizable(False, False)
        CTkLabel(self, text='Project by Ron Katz & Tomer Mazurov', font=('Arial', 20)).place(in_=self, anchor=SE, x=687, y=703)

        container = CTkFrame(self, width=676, height=650)
        container.place(in_=self, x=12, y=12)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.update()

        self.create_frames(container)

        logout_icon = CTkImage(dark_image=Image.open(path + '\\icons\\exit.png'), size=(40, 40))
        self.logout_button = CTkButton(self, text='', image=logout_icon, width=40, height=40,
                                       fg_color=colors['gray_14'], hover_color=colors['gray_14'],
                                       command=self.logout)
        self.logout_button_is_shown = False

        self.show_frame('LoginPage' if connected else 'ConnectionFailedFrame')

    def create_frames(self, container: CTkFrame):
        self.frames: dict[str, CTkFrame] = {}

        for F in (ConnectionFailedFrame, LoginPage, MainPage):
            page_name = F.__name__
            frame: CTkFrame = F(parent=container, controller=self, 
                                width=container.winfo_width(), height=container.winfo_height())
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky=NSEW)

    def show_frame(self, page_name: str):
        if page_name == 'MainPage' and not self.logout_button_is_shown:
            self.logout_button.place(in_=self, anchor=SW,x=12, y=714)
            self.logout_button_is_shown = True
        else:
            if self.logout_button_is_shown:
                self.logout_button.place_forget()
                self.logout_button_is_shown = False

        frame = self.frames.get(page_name)
        frame._canvas.event_generate('<<ShowFrame>>')
        frame.tkraise()

    def connect_to_server(self, addr):
        try:
            self.client = Client(addr)
        except ConnectionFailedError:
            return False
        return True
    
    def signup(self, username: str, password: str):
        return self.client.send_signup_request(username, password)

    def login(self, username: str, password: str):
        response = self.client.send_login_request(username, password)
        if response[0]:
            self.username = username
            self.userfiles = response[1]
            self.title(f'Connected as {username}')
            self.show_frame('MainPage')

        return response
        
    def logout(self):
        confirmed_with_server = self.client.notify_logout()
        if not confirmed_with_server:
            CTkMessagebox(self, title='An Error Occured', 
                          message='An Error occured trying to logout.\nPlease try again',
                          icon='cancel').get()
            return
        self.username = ''
        self.userfiles.clear()
        self.title(DEFAULT_TITLE)
        self.show_frame('LoginPage')

    def upload_file(self, file_path: str, is_public: bool, status_text: StringVar):
        allowed = self.client.send_upload_request(file_path, is_public)
        if not allowed[0]:
            status_text.set(allowed[1])
            return (False, '')
        
        status_text.set('Uploading File...')
        uploaded = self.client.upload_file(file_path)

        status_text.set('Upload Completed' if uploaded[0] else 'Upload Failed')
        return uploaded
    
    def download_file(self, file_name: str, username: str = ''):
        if not username:
            username = self.username
        
        allowed = self.client.send_download_request(username, file_name)
        if not allowed[0]:
            self.show_download_failed(file_name, allowed[1])
            return False
        
        downloaded = self.client.download_file(file_name)
        if not downloaded:
            self.show_download_failed(file_name, 'Internal server error, please try again')
            return False
        
        return username == self.username

    def show_download_failed(self, file_name: str, reason: str):
        CTkMessagebox(self, title='Could Not Download File',
            message=f'Could not download {file_name}\nReason: {reason}',
            icon='CANCEL').get()

    def update_publicity(self, file_name: str):
        return self.client.change_file_publicity(file_name)
    
    def delete_file(self, file_name: str):
        return self.client.delete_file(file_name)
    
    def search_users(self, search_key: str):
        result = self.client.search_users(search_key)
        if not result[0]:
            CTkMessagebox(self, title='An Error Occured', 
                          message='An Error occured trying to search_users.\nPlease try again',
                          icon='cancel').get()
            return {}
        
        return result[1]
    
    def get_user_files(self, username: str):
        result = self.client.get_user_files(username)
        if not result[0]:
            CTkMessagebox(self, title='An Error Occured', 
                          message='An Error occured trying to get user_files.\nPlease try again',
                          icon='cancel').get()
            return None
        
        return result[1]

    def lock(self):
        self.focus_set()
        self.attributes('-disabled', True)

    def free(self):
        self.attributes('-disabled', False)

def main():
    GUI(('127.0.0.1', 17293)).mainloop()

if __name__ == '__main__':
    main()