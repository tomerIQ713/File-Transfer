from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image

from utils import colors, path

#import frames
from frames.togglable_file_box import TogglableFileBox
from frames.upload_window import UploadWindow

class MyFilesFrame(CTkFrame):
    def __init__(self, parent: CTkFrame, controller, main, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main
        self.configure(fg_color=colors['gray_20'])

        CTkLabel(self, text='My Files', font=('Arial', 24)).place(in_=self, x=10, y=6)

        upload_icon = CTkImage(dark_image=Image.open(path + '\\icons\\upload.png'), size=(25, 25))
        self.upload_button = CTkButton(self, text='', image=upload_icon, width=25, height=25,
                                       fg_color=colors['gray_20'], hover_color=colors['gray_20'],
                                       command=self.show_upload_window)
        self.upload_button.place(in_=self, anchor=NE, x=673, y=5)

        search_icon = CTkImage(dark_image=Image.open(path + '\\icons\\magnifying_glass.png'), size=(40, 40))
        CTkLabel(self, text='', image=search_icon).place(in_=self, x=0, y=35)

        self.file_search = CTkEntry(self, width=631, height=25, corner_radius=0, border_width=0, font=('Arial', 16),
                                    fg_color=colors['gray_32'], text_color=colors['white'],
                                    placeholder_text='Search my files', placeholder_text_color=colors['gray_52'])
        self.file_search.place(in_=self, x=35, y=43)
        self.file_search.bind('<Return>', self.search_files)

        self.file_list = CTkScrollableFrame(self, width=652, height=516, fg_color=colors['gray_24'], corner_radius=0)
        self.file_list.place(in_=self, x=4, y=78)
        
        self.bind('<<ShowFrame>>', self.load_files)

    def load_files(self, *args):
        for file in self.file_list.winfo_children():
            file.destroy()
        self.file_search.delete(0, END)

        files = self.main.userfiles[::-1]
        self.filebox_list: list[TogglableFileBox] = []
        for file in files:
            f = TogglableFileBox(self.file_list, controller=self, main=self.main, file=file,
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

        not_yet_shown: list[TogglableFileBox] = list.copy(self.filebox_list)
        for file in not_yet_shown:
            if file.get_file_name().lower().startswith(search_key):
                file.pack(padx=5, pady=3)
                not_yet_shown.remove(file)

        for file in not_yet_shown:
            if search_key in file.get_file_name().lower():
                file.pack(padx=5, pady=3)

    def show_upload_window(self):
        UploadWindow(self, self.main, width=500, height=140, fg_color=colors['gray_14'])
    
    def add_file(self, file_data: dict):
        self.main.userfiles.append(file_data)
        f = TogglableFileBox(self.file_list, controller=self, main=self.main, file=file_data, 
                    width=642, height=60,
                    fg_color=colors['gray_32'], corner_radius=0)
        
        if len(self.filebox_list) > 0:
            f.pack(padx=5, pady=3, before=self.file_list.winfo_children()[0])
        else:
            f.pack(padx=5, pady=3)
        self.filebox_list.insert(0, f)

    def delete_file(self, file_name: str):
        file = None
        for f in self.filebox_list:
            if f.file_name == file_name:
                file = f
                break

        if not file:
            return
        
        confirmed_with_server = self.main.delete_file(file_name)
        if confirmed_with_server:
            file.destroy()
            return
        
        CTkMessagebox(self, title='An Error Occured',
                      message=f'An Error occured trying to delete {file_name}\nPlease try again.',
                      icon='cancel').get()