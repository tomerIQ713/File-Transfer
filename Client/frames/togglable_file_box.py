from customtkinter import *
from CTkMessagebox import CTkMessagebox

from PIL import Image

from utils import colors, path, get_upload_date, bytes_to_higher

class TogglableFileBox(CTkFrame):
    def __init__(self, parent: CTkFrame, controller, main, file: dict, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main

        self.configure(width=642, height=60)
        
        self.expand_icon = CTkImage(dark_image=Image.open(path + '\\icons\\arrow_down.png'), size=(28, 15))
        self.collapse_icon = CTkImage(dark_image=Image.open(path + '\\icons\\arrow_up.png'), size=(28, 15))
        self.toggled = False        
        
        self.toggle_button = CTkButton(self, text='', image=self.expand_icon, width=28, height=15,
                                       fg_color=colors['gray_32'], hover_color=colors['gray_32'],
                                       command=self.toggle)
        self.toggle_button.place(in_=self, anchor=W, x=2, y=29)        
        
        self.file_name: str = file['file-name']
        CTkLabel(self, text=self.file_name, font=('Arial', 16)).place(in_=self, anchor=W, x=48, y=29)

        download_icon = CTkImage(dark_image=Image.open(path + '\\icons\\download.png'), size=(36, 34))
        self.download_button = CTkButton(self, text='', image=download_icon, width=36, height=34,
                                         fg_color=colors['gray_32'], hover_color=colors['gray_32'],
                                         command=self.download)
        self.download_button.place(in_=self, anchor=NE, x=638, y=9)

        CTkLabel(self, text=get_upload_date(file['upload-time']), font=('Arial', 16)).place(in_=self, anchor=E, x=582, y=29)
        CTkLabel(self, text=bytes_to_higher(file['file-size-bytes']), font=('Arial', 16)).place(in_=self, anchor=E, x=490, y=29)

        self.subframe = CTkFrame(self, width=622, height=36, fg_color=colors['gray_28'], corner_radius=0)
        self.subframe.place(in_=self, x=10, y=60)

        CTkLabel(self.subframe, text='Public:', font=('Arial', 14)).place(in_=self.subframe, anchor=W, x=5, y=17)
        self.public_checkbox = CTkCheckBox(self.subframe, text='', width=10, height=10,
                                           border_color=colors['white'], hover_color=colors['white'],
                                           checkmark_color=colors['gray_28'], fg_color=colors['white'],
                                           command=self.toggle_publicity)
        if file['is-public']:
            self.public_checkbox.select()
        self.public_checkbox.place(in_=self.subframe, anchor=W, x=50, y=17)

        self.download_count = StringVar(value=f'Downloads: {file['download-count']}')
        CTkLabel(self.subframe, textvariable=self.download_count, font=('Arial', 14)).place(in_=self.subframe, anchor=W, x=85, y=17)

        delete_icon = CTkImage(dark_image=Image.open(path + '\\icons\\trash_can.png'), size=(22, 24))
        self.delete_button = CTkButton(self.subframe, text='', image=delete_icon, width=22, height=24,
                                       fg_color=colors['gray_28'], hover_color=colors['gray_28'],
                                       command=self.delete)
        self.delete_button.place(in_=self.subframe, anchor=E, x=620, y=17)

    def toggle(self):
        self.toggle_button.configure(image=self.expand_icon if self.toggled else self.collapse_icon)
        self.toggled = not self.toggled

        height = self.winfo_height()
        if self.toggled:
            self.configure(height=height+37)
        else:
            self.configure(height=height-37)

    def toggle_publicity(self):
        confirmed_with_server = self.main.update_publicity(self.file_name)
        if not confirmed_with_server:
            CTkMessagebox(self, title='An Error Occured',
                          message=f'An Error occured trying to change {self.file_name}\'s publicity status\nPlease try again.',
                          icon='cancel').get()

            s = self.public_checkbox.get()
            if s:
                self.public_checkbox.deselect()
            else:
                self.public_checkbox.select()

    def delete(self):
        msgbox = CTkMessagebox(self, title='Delete File', message=f'Are you sure you want to delete {self.file_name}?',
                                     icon="question", option_1='Delete', option_2='Cancel')
        confirmation = msgbox.get()
        if confirmation != 'Delete':
            return    
            
        self.controller.delete_file(self.file_name)

    def download(self):
        increment = self.main.download_file(self.file_name)
        if increment:
            download_count = int(self.download_count.get().split(': ')[1]) + 1
            self.download_count.set(f'Downloads: {download_count}')

    def get_file_name(self):
        return os.path.splitext(self.file_name)[0]
    