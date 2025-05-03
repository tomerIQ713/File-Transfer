from customtkinter import *
from PIL import Image

from utils import Colors, PATH, FONT

#import frames
from frames.my_files_page import MyFilesPage
from frames.user_search_page import UserSearchPage

class MainPage(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color='transparent')

        search_container = CTkFrame(self, fg_color='transparent')
        search_container.pack(fill=X)

        search_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\magnifying_glass.png'), size=(40, 40))
        CTkLabel(search_container, text='', image=search_icon).pack(side=LEFT)

        self.user_search = CTkEntry(search_container, height=40, border_width=0, font=(FONT, 20),
                                    fg_color=Colors.gray_20, text_color=Colors.gray_92,
                                    placeholder_text='Search users', placeholder_text_color=Colors.gray_40)
        self.user_search.pack(pady=(0, 5), fill=X)
        self.user_search.bind('<Return>', self.search_users)
        self.search_key = ''

        container = CTkFrame(self, fg_color='transparent')
        container.grid_rowconfigure(0, weight=1)            
        container.grid_columnconfigure(0, weight=1)    
        container.pack(pady=(5, 0), fill=BOTH, expand=1)
        self.update()

        self.create_frames(container)
        self.bind('<<ShowFrame>>', self.on_frame_show)

    def on_frame_show(self, *args):
        self.user_search.delete(0, END)
        self.search_key = ''
        self.matching_users = []
        self.show_frame('MyFilesPage')

    def create_frames(self, container: CTkFrame):
        self.frames: dict[str, CTkFrame] = {}

        for F in (MyFilesPage, UserSearchPage):
            page_name = F.__name__
            frame: CTkFrame = F(parent=container, controller=self, main=self.controller)            
            frame.grid(row=0, column=0, sticky=NSEW)
            self.frames[page_name] = frame

    def show_frame(self, page_name: str):
        frame = self.frames.get(page_name)
        frame._canvas.event_generate('<<ShowFrame>>')
        frame.tkraise()
    
    def search_users(self, *args):
        search_key = self.user_search.get()
        if search_key == self.search_key:
            return
        self.search_key = search_key
        
        if not search_key:
            self.matching_users.clear()
            self.show_frame('MyFilesPage')
        
        else:
            accepted, users = self.controller.search_users(search_key)
            if accepted:
                self.matching_users = users
                self.show_frame('UserSearchPage')