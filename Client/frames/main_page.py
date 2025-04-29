from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image
import re

from utils import colors, path

#import frames
from frames.my_files import MyFilesFrame
from frames.user_search import UserSearchFrame

class MainPage(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color=colors['gray_14'])

        search_icon = CTkImage(dark_image=Image.open(path + '\\icons\\magnifying_glass.png'), size=(40, 40))
        CTkLabel(self, text='', image=search_icon).place(in_=self, x=0, y=0)

        self.user_search = CTkEntry(self, width=636, height=40, corner_radius=0, border_width=0, font=('Arial', 20),
                                    fg_color=colors['gray_20'], text_color=colors['white'],
                                    placeholder_text='Search for other users', placeholder_text_color=colors['gray_40'])
        self.user_search.place(in_=self, anchor=NW, x=40, y=0)
        self.user_search.bind('<Return>', self.search_users)
        self.search_key = ''

        container = CTkFrame(self, width=676, height=598, corner_radius=0)
        container.place(in_=self, x=0, y=52)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.update()

        self.create_frames(container)
        self.bind('<<ShowFrame>>', self.on_frame_show)

    def on_frame_show(self, *args):
        self.user_search.delete(0, END)
        self.search_key = ''
        self.show_frame('MyFilesFrame')

    def create_frames(self, container: CTkFrame):
        self.frames: dict[str, CTkFrame] = {}

        for F in (MyFilesFrame, UserSearchFrame):
            page_name = F.__name__
            frame: CTkFrame = F(parent=container, controller=self, main=self.controller,
                                width=container.winfo_width(), height=container.winfo_height(),
                                corner_radius=0)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky=NSEW)

    def show_frame(self, page_name: str):
        frame = self.frames.get(page_name)
        frame._canvas.event_generate('<<ShowFrame>>')
        frame.tkraise()

    def search_users(self, *args):
        search_key = self.user_search.get()
        if search_key == self.search_key:
            return
        
        if search_key and not re.match(r'^[a-z0-9]+$', search_key) or len(search_key) > 16:
            CTkMessagebox(self, title='Invalid Search Key',
                          message='Usernames can only contain lowercase letters and numbers, and must be 16 characters or less').get()
            return

        self.search_key = search_key

        if not search_key:
            self.show_frame('MyFilesFrame')

        else:
            self.found_users = self.controller.search_users(search_key)
            self.show_frame('UserSearchFrame')