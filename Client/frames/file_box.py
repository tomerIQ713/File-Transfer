from customtkinter import *
from CTkMessagebox import CTkMessagebox
from PIL import Image

from utils import Colors, PATH, FONT, get_upload_date, bytes_to_higher

class FileBox(CTkFrame):
    def __init__(self, parent, controller, main, file: dict, include_subframe: bool, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.main = main
        
        self.include_subframe = include_subframe
        self.file = file
        
        self.title_frame = CTkFrame(self, fg_color=Colors.gray_32)
        self.title_frame.pack(fill=X)

        if (self.include_subframe):
            self.prepare_subframe()

        CTkLabel(self.title_frame, text=self.file['file-name'], font=(FONT, 20)).pack(side=LEFT, padx=10)

        download_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\download.png'), size=(36, 34))
        self.download_button = CTkButton(self.title_frame, text='', image=download_icon, width=36, height=34,
                                         fg_color='transparent', hover_color=Colors.gray_72,
                                         command=self.download)
        self.download_button.pack(side=RIGHT, padx=10, pady=10)

        CTkFrame(self.title_frame, width=2, height=50, fg_color=Colors.gray_40).pack(side=RIGHT, pady=5, fill=Y) #divider
        CTkLabel(self.title_frame, text=get_upload_date(file['upload-time']), font=(FONT, 20)).pack(side=RIGHT, padx=10)

        CTkFrame(self.title_frame, width=2, height=50, fg_color=Colors.gray_40).pack(side=RIGHT, pady=5, fill=Y) #divider
        CTkLabel(self.title_frame, text=bytes_to_higher(file['file-size-bytes']), font=(FONT, 20)).pack(side=RIGHT, padx=10)

    def download(self):
        increment = self.controller.download_file(self)
        if self.include_subframe and increment:
            self.download_count.set(f'Downloads: {self.file['download-count']}')

    def prepare_subframe(self):
        self.subframe = CTkFrame(self, height=30, fg_color=Colors.gray_28)

        self.expand_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\arrow_down.png'), size=(28, 15))
        self.collapse_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\arrow_up.png'), size=(28, 15))
        self.toggled = False

        self.toggle_button = CTkButton(self.title_frame, text='', image=self.expand_icon, width=28, height=25,
                                       fg_color='transparent', hover_color=Colors.gray_72,
                                       command=self.toggle)
        self.toggle_button.pack(side=LEFT, padx=10, pady=10)

        self.public_checkbox = CTkCheckBox(self.subframe, text='Public', font=(FONT, 16), width=10, height=10,
                                         border_color=Colors.gray_72, hover_color=Colors.gray_72,
                                         checkmark_color=Colors.gray_28, fg_color=Colors.gray_72,
                                         command=self.toggle_publicity)
        self.public_checkbox.pack(side=LEFT, padx=5, pady=5)
        if self.file['is-public']:
            self.public_checkbox.select()

        CTkFrame(self.subframe, width=2, height=26, fg_color=Colors.gray_32).pack(side=LEFT, pady=2, fill=Y) #divider
        self.download_count = StringVar(value=f'Downloads: {self.file['download-count']}')
        CTkLabel(self.subframe, textvariable=self.download_count, font=(FONT, 16)).pack(side=LEFT, padx=5)

        delete_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\trash_can.png'), size=(22, 24))
        self.delete_button = CTkButton(self.subframe, text='', image=delete_icon, width=22, height=24,
                                       fg_color='transparent', hover_color=Colors.gray_52,
                                       command=self.delete_file)
        self.delete_button.pack(side=RIGHT, padx=5, pady=5)

    def toggle(self):
        if not self.include_subframe: return

        self.toggled = not self.toggled
        self.toggle_button.configure(image=self.collapse_icon if self.toggled else self.expand_icon)
        
        if self.toggled:
            self.subframe.pack(padx=10, fill=X)
        else:
            self.subframe.pack_forget()

    def toggle_publicity(self):
        if not self.include_subframe: return

        confirmed = self.main.change_file_publicity(self.file['file-name'])
        if not confirmed:
            #undo action
            s = self.public_checkbox.get()
            if s:
                self.public_checkbox.deselect()
            else:
                self.public_checkbox.select()

    def delete_file(self):
        if not self.include_subframe: return

        msg_box = CTkMessagebox(self, title='Delete File', message=f'Are you sure you want to delete {self.file['file-name']}?',
                                icon='question', option_1='Delete', option_2='Cancel')
        confirmation = msg_box.get()
        if confirmation == 'Delete':
            self.controller.delete_file(self)