from customtkinter import *
from PIL import Image

from utils import Colors, PATH, FONT

#import frames
from frames.user_box import UserBox

class UserSearchPage(CTkFrame):
    def __init__(self, parent, controller, main, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main
        self.configure(fg_color=Colors.gray_20)

        header = CTkFrame(self, fg_color='transparent')
        header.pack(padx=6, pady=6, fill=X)
        
        self.title = StringVar()
        CTkLabel(header, textvariable=self.title, font=(FONT, 24)).pack(side=LEFT)

        self.user_list = CTkScrollableFrame(self, fg_color=Colors.gray_24)
        self.user_list.pack(padx=6, pady=6, fill=BOTH, expand=1)

        self.bind('<<ShowFrame>>', self.on_frame_show)

    def on_frame_show(self, *args):
        for user in self.user_list.winfo_children():
            user.destroy()

        self.title.set(f'Showing results for {self.controller.search_key}')

        users: dict[str, int] = self.controller.matching_users
        for username, file_count in users.items():
            u = UserBox(self.user_list, controller=self, main=self.main, user=(username, file_count),
                        height=60, fg_color=Colors.gray_32)
            u.pack(padx=6, pady=2, fill=X)