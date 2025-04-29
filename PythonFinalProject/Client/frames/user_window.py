from customtkinter import *

from PIL import Image

from utils import colors, path

from frames.flie_box import FileBox

class UserWindow(CTkToplevel):
    def __init__(self, controller, main, userdata: dict, *args, **kwargs):
        CTkToplevel.__init__(self, *args, **kwargs)
        self.controller = controller
        self.main = main
        self.username = userdata['username']

        self.main.lock()
        self.attributes("-topmost", True)
        self.title(f'{self.username}\'s Files')
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.geometry('662x622')
        self.resizable(False, False)

        container = CTkFrame(self, width=638, height=598, corner_radius=0, fg_color=colors['gray_20'])
        container.place(in_=self, x=12, y=12)
        CTkLabel(container, text=f'{self.username}\'s Files', font=('Arial', 24)).place(in_=container, x=10, y=6)

        search_icon = CTkImage(dark_image=Image.open(path + '\\icons\\magnifying_glass.png'), size=(40, 40))
        CTkLabel(container, text='', image=search_icon).place(in_=container, x=0, y=35)

        self.file_search = CTkEntry(container, width=593, height=25, corner_radius=0, border_width=0, font=('Arial', 16),
                                    fg_color=colors['gray_32'], text_color=colors['white'],
                                    placeholder_text=f'Search {self.username}\'s files', placeholder_text_color=colors['gray_52'])
        self.file_search.place(in_=container, x=35, y=43)
        self.file_search.bind('<Return>', lambda: None)
        
        self.file_list = CTkScrollableFrame(container, width=614, height=516, fg_color=colors['gray_24'], corner_radius=0)
        self.file_list.place(in_=container, x=4, y=76)

        self.load_files(userdata['files'])

    def load_files(self, user_files: list):
        user_files = user_files[::-1]
        self.filebox_list: list[FileBox] = []
        print(user_files)
        for file in user_files:
            f = FileBox(self.file_list, controller=self, main=self.main, file=file,
                        fg_color=colors['gray_32'], corner_radius=0)
            f.pack(padx=5, pady=3)
            self.filebox_list.append(f)

    def search_files(self, *args):
        for file in self.filebox_list:
            file.pack_forget()

        search_key = self.file_search.get().lower()
        if not search_key:
            for file in self.filebox_list:
                file.pack(padx=5, pady=3)
            return
        
        not_yet_shown: list[FileBox] = list.copy(self.filebox_list)        
        for file in not_yet_shown:
            if file.get_file_name().lower().startswith(search_key):
                file.pack(padx=5, pady=3)
                not_yet_shown.remove(file)

        for file in not_yet_shown:
            if search_key in file.get_file_name().lower():
                file.pack(padx=5, pady=3)

    def close(self):
        self.main.free()
        self.destroy()