from customtkinter import *

from PIL import Image

from utils import colors, path

class UploadWindow(CTkToplevel):
    def __init__(self, controller, main, *args, **kwargs):
        CTkToplevel.__init__(self, *args, **kwargs)
        self.controller = controller
        self.main = main

        self.main.lock()
        self.attributes("-topmost", True)
        self.title('Upload File')
        self.protocol('WM_DELETE_WINDOW', self.close)

        self.file_path_entry = CTkEntry(self, width=400, height=40, font=('Arial', 20), 
                                   corner_radius=0, border_width=0,
                                   fg_color=colors['gray_20'], text_color=colors['white'])
        self.file_path_entry.place(in_=self, x=70, y=20)

        browse_icon = CTkImage(dark_image=Image.open(path + '\\icons\\browse_files.png'), size=(30, 30))
        self.file_select = CTkButton(self, text='', image=browse_icon, width=40, height=40, corner_radius=0,
                                fg_color=colors['gray_32'], hover_color=colors['gray_32'],
                                command=self.select_file)
        self.file_select.place(in_=self, x=30, y=20)

        self.upload_as_public = CTkCheckBox(self, width=20, height=20,
                                       border_color=colors['white'], hover_color=colors['white'],
                                       checkmark_color=colors['gray_28'], fg_color=colors['white'],
                                       text='Upload as Public', font=('Arial', 14))
        self.upload_as_public.select()
        self.upload_as_public.place(in_=self, x=30, y=75)

        self.upload_button = CTkButton(self, width=100, height=40, text='Upload', font=('Arial', 14),
                                  fg_color=colors['blue'], hover_color=colors['blue_hover'], 
                                  border_width=0, corner_radius=0,
                                  command=self.upload)
        self.upload_button.place(in_=self, anchor=NE, x=330, y=67)

        self.cancel_button = CTkButton(self, width=75, height=40, text='Cancel', font=('Arial', 14),
                                  fg_color=colors['red'], hover_color=colors['red_hover'], 
                                  border_width=0, corner_radius=0,
                                  command=self.close)
        self.cancel_button.place(in_=self, anchor=NE, x=470, y=67)

        self.upload_in_progress = False

        self.response_text = StringVar()
        self.response_label = CTkLabel(self, textvariable=self.response_text, font=('Arial', 16))
        self.response_label.place(in_=self, anchor=N, relx=0.5, y=110)

    def close(self):
        self.main.free()
        self.destroy()

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_entry.delete(0, END)
            self.file_path_entry.insert(0, file_path)

    def upload(self):
        self.response_label.configure(text_color=colors['white'])
        file_path = self.file_path_entry.get()
        
        self.upload_in_progress = True
        result = self.main.upload_file(file_path.replace('/', '\\'), bool(self.upload_as_public.get()), self.response_text)
        self.response_label.configure(text_color=colors['text_green' if result[0] else 'text_red'])
        self.upload_in_progress = False
        
        if result[0]:
            self.controller.add_file(result[1])
            self.close()