from customtkinter import *

from utils import colors

from frames.user_box import UserBox

class UserSearchFrame(CTkFrame):
    def __init__(self, parent: CTkFrame, controller, main, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main
        self.configure(fg_color=colors['gray_20'])

        self.title = StringVar()
        CTkLabel(self, textvariable=self.title, font=('Arial', 24)).place(in_=self, x=10, y=6)

        self.user_list = CTkScrollableFrame(self, width=652, height=554, fg_color=colors['gray_24'], corner_radius=0)
        self.user_list.place(in_=self, x=4, y=40)

        self.bind('<<ShowFrame>>', self.on_frame_show)

    def on_frame_show(self, *args):
        for user in self.user_list.winfo_children():
            user.destroy()
        
        self.title.set(f'Showing Results for "{self.controller.search_key}"')
        
        users: list[str] = self.controller.found_users

        for username, file_count in users.items():
            u = UserBox(self.user_list, controller=self, main=self.main, user=(username, file_count), 
                        width=642, height=60,
                        fg_color=colors['gray_32'], corner_radius=0)
            u.pack(padx=5, pady=3)