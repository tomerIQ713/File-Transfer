from customtkinter import *

from PIL import Image

from utils import colors, path

from frames.user_window import UserWindow

class UserBox(CTkFrame):
    def __init__(self, parent: CTkFrame, controller, main, user: tuple[str, int], *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main

        user_icon = CTkImage(dark_image=Image.open(path + '\\icons\\user_icon.png'), size=(34, 43))
        self.select_user_button = CTkButton(self, text='', image=user_icon, width=34, height=43,
                                            fg_color=colors['gray_32'], hover_color=colors['gray_32'],
                                            command=self.show_user_window)
        self.select_user_button.place(in_=self, x=-1, y=5)
        
        self.username: str = user[0]
        CTkLabel(self, text=self.username, font=('Arial', 16)).place(in_=self, anchor=W, x=48, y=29)

        file_count_icon = CTkImage(dark_image=Image.open(path + '\\icons\\file_count.png'), size=(30, 20))
        CTkLabel(self, text='', image=file_count_icon).place(in_=self, anchor=NE, x=633, y=5)
        CTkLabel(self, text=user[1], font=('Arial', 24)).place(in_=self, anchor=NE, x=633, y=30)

    def show_user_window(self):
        user_files = self.main.get_user_files(self.username)
        if user_files == None:
            return
        UserWindow(self, self.main, {'username': self.username, 
                                     "files": user_files
                                    }, fg_color=colors['gray_14'])