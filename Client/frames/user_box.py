from customtkinter import *
from PIL import Image

from utils import Colors, PATH, FONT

class UserBox(CTkFrame):
    def __init__(self, parent, controller, main, user: tuple[str, int], *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main

        self.username = user[0]

        user_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\user_icon.png'), size=(30, 40))
        self.select_user = CTkButton(self, text='', image=user_icon, width=30, height=40,
                                     fg_color='transparent', hover_color=Colors.gray_72,
                                     command=self.show_user_window)
        self.select_user.pack(side=LEFT, padx=10, pady=10)

        CTkLabel(self, text=self.username, font=(FONT, 20)).pack(side=LEFT, padx=10)

        files_container = CTkFrame(self, fg_color='transparent')
        files_container.pack(side=RIGHT, padx=10, pady=10)

        file_count_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\file_count.png'), size=(30, 20))
        CTkLabel(files_container, text='', image=file_count_icon).pack(anchor=E)
        CTkLabel(files_container, text=user[1], font=(FONT, 24)).pack(anchor=E)

    def show_user_window(self):
        self.main.show_user_window(self.username)