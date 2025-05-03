from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image

from client import Client
from utils import Colors, PATH, TITLE, FONT

#import frames
from frames.connection_fail_page import ConnectionFailPage
from frames.login_page import LoginPage
from frames.main_page import MainPage
from frames.user_window import UserWindow

class GUI(CTk):
    def __init__(self, addr, *args, **kwargs):
        FontManager.load_font(PATH + '\\resources\\RobotoSlab-Regular.ttf')

        CTk.__init__(self, fg_color=Colors.gray_14, *args, **kwargs)
        connected = self.connect_to_server(addr)
        self.userfiles = []
        self.user_windows: dict[str, UserWindow] = {}

        self.title(TITLE)
        self.geometry('700x720')
        self.minsize(700, 720)
        
        container = CTkFrame(self, fg_color='transparent')
        container.grid_rowconfigure(0, weight=1)            
        container.grid_columnconfigure(0, weight=1)    
        container.pack(padx=10, pady=(10, 0), fill=BOTH, expand=1)
        self.update()

        footer = CTkFrame(self, height=60, fg_color='transparent')
        footer.pack_propagate(False)
        footer.pack(padx=10, fill=X)
        CTkLabel(footer, text=TITLE, font=(FONT, 24)).pack(side=RIGHT, pady=5) #footer text

        logout_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\exit.png'), size=(40, 40))
        self.logout_button = CTkButton(footer, text='', image=logout_icon, width=40, height=40,
                                       fg_color='transparent', hover_color=Colors.gray_32,
                                       command=self.logout)
        self.logout_button_is_shown = False

        self.create_frames(container)
        self.show_frame('LoginPage' if connected else 'ConnectionFailPage')

    def create_frames(self, container: CTkFrame):
        self.frames: dict[str, CTkFrame] = {}

        for F in (ConnectionFailPage, LoginPage, MainPage):
            page_name = F.__name__
            frame: CTkFrame = F(parent=container, controller=self)            
            frame.grid(row=0, column=0, sticky=NSEW)
            self.frames[page_name] = frame

    def show_frame(self, page_name: str):
        frame = self.frames.get(page_name)
        frame._canvas.event_generate('<<ShowFrame>>')
        frame.tkraise()

    def show_message_box(self, title: str, message: str, icon: str):
        CTkMessagebox(self, title=title, message=message, icon=icon).get()

    def connect_to_server(self, addr):
        try:
            self.client = Client(addr)
            return True
        except ConnectionError as e:
            return False

    def login(self, username: str, password: str):
        accepted, response = self.client.send_login_package(username, password)

        if accepted:
            self.set_properties_after_login(username, response)

        return (accepted, response)
    
    def signup(self, username: str, password: str):
        accepted, response = self.client.send_signup_package(username, password)

        if accepted:
            self.set_properties_after_login(username, [])

        return (accepted, response)
    
    def set_properties_after_login(self, username: str, userfiles: list):
        self.username = username
        self.userfiles = userfiles
        self.title(f'Connected as {username}')
        self.logout_button.pack(side=LEFT, pady=10)
        self.show_frame('MainPage')

    def logout(self):
        accepted, response = self.client.send_logout_package()
        if accepted:
            self.username = ''
            self.userfiles.clear()
            self.title(TITLE)
            self.logout_button.pack_forget()
            self.show_frame('LoginPage')

            for user_window in self.user_windows.values():
                user_window.destroy()
            self.user_windows.clear()

        else:
            self.show_message_box('Logout failed', response, 'cancel')      

    def upload_file(self, file_path: str, is_public: bool):
        accepted, response = self.client.send_upload_request(file_path, is_public)
        if not accepted:
            self.show_message_box('Upload Request Denied', response, 'cancel')
            return (False, {})
        
        uploaded, file_data = self.client.upload_file(file_path)
        if not accepted:
            self.show_message_box('Upload Failed', response, 'cancel')
            return (False, {})
        
        self.userfiles.append(file_data)
        return (uploaded, file_data)
    
    def download_file(self, file: dict, username: str = ''):
        if not username: username = self.username

        accepted, response = self.client.send_download_request(file['file-name'], username)
        if not accepted:
            self.show_message_box('Download Request Denied', response, 'cancel')
            return False

        downloaded = self.client.download_file(file['file-name'])
        if not downloaded:
            self.show_message_box('Download Failed', 'Failed to download file', 'cancel')
            return False

        if username == self.username:
            index = self.userfiles.index(file)
            self.userfiles[index]['download-count'] += 1
        return True

    def change_file_publicity(self, file_name: str):
        accepted, response = self.client.send_file_publicity_change_request(file_name)

        if not accepted:
            self.show_message_box('Change Failed', response, 'cancel')
        return accepted
    
    def delete_file(self, file: dict):
        accepted, response = self.client.send_file_deletion_request(file['file-name'])

        if accepted:                    
            self.userfiles.remove(file)
        else:
            self.show_message_box('Deletion Failed', response, 'cancel')

        return accepted
    
    def search_users(self, search_key: str):
        accepted, response = self.client.send_user_search_request(search_key)
        
        if not accepted:
            self.show_message_box('Search Failed', response, 'cancel')

        return (accepted, response)
    
    def show_user_window(self, username: str):
        if username in self.user_windows:
            self.user_windows[username].lift()
        else:
            u = UserWindow(self, username)
            self.user_windows[username] = u
            u.lift()

    def get_user_files(self, username: str):
        accepted, response = self.client.send_user_files_request(username)
        
        if not accepted:
            self.show_message_box('Failed To Retrieve Files', response, 'cancel')

        return (accepted, response)

    def user_window_closed(self, username: str):
        self.user_windows.pop(username)

def main():
    GUI(('192.168.1.113', 11111)).mainloop()

if __name__ == '__main__':
    main()