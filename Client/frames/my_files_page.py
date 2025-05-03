from customtkinter import *
from PIL import Image

from utils import Colors, PATH, FONT

#import frames
from frames.file_box import FileBox
from frames.upload_window import UploadWindow

class MyFilesPage(CTkFrame):
    def __init__(self, parent, controller, main, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main
        self.configure(fg_color=Colors.gray_20)

        self.upload_window: UploadWindow = None

        header = CTkFrame(self, fg_color='transparent')
        header.pack(padx=6, pady=6, fill=X)
        CTkLabel(header, text='My Files', font=(FONT, 24)).pack(side=LEFT)
        
        upload_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\upload.png'), size=(24, 24))
        self.upload_button = CTkButton(header, text='', image=upload_icon, width=24, height=24,
                                       fg_color='transparent', hover_color=Colors.gray_32,
                                       command=self.show_upload_window)
        self.upload_button.pack(side=RIGHT)

        search_container = CTkFrame(self, fg_color='transparent')
        search_container.pack(padx=6, pady=6, fill=X)

        search_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\magnifying_glass.png'), size=(32, 32))
        CTkLabel(search_container, text='', image=search_icon).pack(side=LEFT)

        self.file_search = CTkEntry(search_container, height=32, border_width=0, font=(FONT, 16),
                                    fg_color=Colors.gray_32, text_color=Colors.gray_92,
                                    placeholder_text='Search my files', placeholder_text_color=Colors.gray_52)
        self.file_search.pack(fill=X)

        self.file_list = CTkScrollableFrame(self, fg_color=Colors.gray_24)
        self.file_list.pack(padx=6, pady=6, fill=BOTH, expand=1)

        self.bind('<<ShowFrame>>', self.load_files)

    def load_files(self, *args):
        for file in self.file_list.winfo_children():
            file.destroy()
        self.file_search.delete(0, END)

        files = self.main.userfiles[::-1] #reverse list to sort from newest to oldest
        self.filebox_list: list[FileBox] = []
        for file in files:
            f = FileBox(self.file_list, controller=self, main=self.main, file=file, include_subframe=True,
                        height=60, fg_color='transparent')
            f.pack(padx=6, pady=2, fill=X)
            self.filebox_list.append(f)    
        
    def show_upload_window(self):
        if self.upload_window is None:
            self.upload_window = UploadWindow(controller=self, main=self.main, fg_color=Colors.gray_14)
        else:
            self.upload_window.lift()

    def add_file(self, file: dict):
        f = FileBox(self.file_list, controller=self, main=self.main, file=file, include_subframe=True,
                    height=60, fg_color='transparent')
        
        if (len(self.filebox_list) == 0):
            f.pack(padx=6, pady=2, fill=X)
            self.filebox_list.append(f)
        else:
            f.pack(padx=6, pady=2, fill=X, before=self.filebox_list[0])
            self.filebox_list.insert(0, f)

    def download_file(self, filebox: FileBox):
        return self.main.download_file(filebox.file)

    def delete_file(self, filebox: FileBox):
        accepted = self.main.delete_file(filebox.file)

        if accepted:
            self.filebox_list.remove(filebox)
            filebox.destroy()
