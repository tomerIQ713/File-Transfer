from customtkinter import *
from PIL import Image

from utils import Colors, PATH, FONT

#import frames
from frames.file_box import FileBox

class UserWindow(CTkToplevel):
    def __init__(self, controller, username: str, *args, **kwargs):
        CTkToplevel.__init__(self, *args, **kwargs)
        self.controller = controller
        self.username = username

        self.title(f'{self.username}\'s Files')
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.geometry('700x612')
        self.minsize(700, 612)

        container = CTkFrame(self, fg_color=Colors.gray_20)
        container.pack(padx=10, pady=10, fill=BOTH, expand=1)

        header = CTkFrame(container, fg_color='transparent')
        header.pack(padx=6, pady=6, fill=X)
        CTkLabel(header, text=f'{self.username}\'s Files', font=(FONT, 24)).pack(side=LEFT)

        refresh_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\refresh.png'), size=(24, 24))
        self.refresh_button = CTkButton(header, text='', image=refresh_icon, width=24, height=24,
                                        fg_color='transparent', hover_color=Colors.gray_32,
                                        command=self.refresh)
        self.refresh_button.pack(side=RIGHT)

        search_container = CTkFrame(container, fg_color='transparent')
        search_container.pack(padx=6, pady=6, fill=X)

        search_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\magnifying_glass.png'), size=(32, 32))
        CTkLabel(search_container, text='', image=search_icon).pack(side=LEFT)

        self.file_search = CTkEntry(search_container, height=32, border_width=0, font=(FONT, 16),
                                    fg_color=Colors.gray_32, text_color=Colors.gray_92,
                                    placeholder_text=f'Search {self.username}\'s files', placeholder_text_color=Colors.gray_52)
        self.file_search.pack(fill=X)

        self.file_list = CTkScrollableFrame(container, fg_color=Colors.gray_24)
        self.file_list.pack(padx=6, pady=6, fill=BOTH, expand=1)
        self.filebox_list: list[FileBox] = []

        self.refresh()        
        
    def refresh(self):
        accepted, files = self.controller.get_user_files(self.username)
        if not accepted:
            return
        
        self.load_files(files)

    def load_files(self, files):
        for child in self.file_list.winfo_children():
            child.destroy()
        self.filebox_list.clear()

        user_files = files[::-1]
        for file in user_files:
            f = FileBox(self.file_list, controller=self, main=self.controller, file=file, include_subframe=False,
                        height=60, fg_color='transparent')
            f.pack(padx=6, pady=2, fill=X)
            self.filebox_list.append(f)

    def download_file(self, filebox: FileBox):
        return self.controller.download_file(filebox.file, self.username)

    def close(self):
        self.controller.user_window_closed(self.username)
        self.destroy()