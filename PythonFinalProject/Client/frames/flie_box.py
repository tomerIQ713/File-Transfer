from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image

from utils import colors, path, get_upload_date, bytes_to_higher

class FileBox(CTkFrame):
    def __init__(self, parent: CTkFrame, controller, main, file: dict, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main

        self.configure(width=604, height=60)

        self.file_name: str = file['file-name']
        CTkLabel(self, text=self.file_name, font=('Arial', 16)).place(in_=self, anchor=W, x=10, y=29)

        download_icon = CTkImage(dark_image=Image.open(path + '\\icons\\download.png'), size=(36, 34))
        self.download_button = CTkButton(self, text='', image=download_icon, width=36, height=34,
                                         fg_color=colors['gray_32'], hover_color=colors['gray_32'],
                                         command=self.download)
        self.download_button.place(in_=self, anchor=NE, x=600, y=9)

        CTkLabel(self, text=get_upload_date(file['upload-time']), font=('Arial', 16)).place(in_=self, anchor=E, x=544, y=29)
        CTkLabel(self, text=bytes_to_higher(file['file-size-bytes']), font=('Arial', 16)).place(in_=self, anchor=E, x=456, y=29)

    def download(self):
        self.main.download_file(self.file_name, self.controller.username)

    def get_file_name(self):
        return os.path.splitext(self.file_name)[0]