from customtkinter import *
from PIL import Image
import time

from utils import Colors, PATH, FONT

WIDTH = 500
HEIGHT = 200

class UploadWindow(CTkToplevel):
    def __init__(self, controller, main, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller
        self.main = main
        self.attributes("-alpha", 0)
        
        self.grab_set()

        spawn_x = int(self.controller.winfo_width() * .5 + self.controller.winfo_x() - .5 * WIDTH + 7)
        spawn_y = int(self.controller.winfo_height() * .5 + self.controller.winfo_y() - .5 * HEIGHT + 20)

        self.after(10)
        self.geometry(f'{WIDTH}x{HEIGHT}+{spawn_x}+{spawn_y}')
        self.title('Upload File')
        self.minsize(WIDTH, HEIGHT)

        self.protocol('WM_DELETE_WINDOW', self.close)

        self.populate()
        self.fade_in()

        self.lift()

    def populate(self):
        field_container = CTkFrame(self, fg_color=Colors.gray_20)
        field_container.pack(padx=10, pady=(10, 7), fill=X)

        browse_icon = CTkImage(dark_image=Image.open(PATH + '\\resources\\browse_files.png'), size=(30, 30))
        self.file_select = CTkButton(field_container, text='', image=browse_icon, width=40, height=40,
                                     fg_color='transparent', hover_color=Colors.gray_32,
                                     command=self.select_file)
        self.file_select.pack(side=LEFT, padx=(6, 3))

        self.file_path_entry = CTkEntry(field_container, height=40, font=(FONT, 20), border_width=0,
                                        fg_color=Colors.gray_24, text_color=Colors.gray_92)
        self.file_path_entry.pack(padx=(3, 6), pady=(6, 3), fill=X)

        self.upload_as_public = CTkCheckBox(field_container, text='Public', font=(FONT, 16), width=10, height=10,
                                            border_color=Colors.gray_72, hover_color=Colors.gray_72,
                                            checkmark_color=Colors.gray_28, fg_color=Colors.gray_72)
        self.upload_as_public.pack(anchor=W, padx=(3, 6), pady=(3, 6))

        buttons_container = CTkFrame(self, fg_color='transparent')
        buttons_container.pack(pady=7)

        self.upload_button = CTkButton(buttons_container, width=200, height=60, text='Upload', font=(FONT, 16),
                                       fg_color=Colors.blue, hover_color=Colors.blue_hover,
                                       command=self.upload)
        self.upload_button.pack(side=LEFT, padx=10)

        self.cancel_button = CTkButton(buttons_container, width=200, height=60, text='Cancel', font=(FONT, 16),
                                       fg_color=Colors.red, hover_color=Colors.red_hover,
                                       command=self.close)
        self.cancel_button.pack(side=RIGHT, padx=10)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_entry.delete(0, END)
            self.file_path_entry.insert(0, file_path)

    def upload(self):
        file_path = self.file_path_entry.get()
        success, file_data = self.main.upload_file(file_path.replace('/', '\\'), bool(self.upload_as_public.get()))
        if success:
            self.controller.add_file(file_data)
            self.close()

    def fade_in(self):
        for i in range(0, 110, 10):
            if not self.winfo_exists():
                break

            self.attributes("-alpha", i/100)
            self.update()
            time.sleep(1/1000)            

    def fade_out(self):
        for i in range(100, 0, -10):
            if not self.winfo_exists():
                break

            self.attributes("-alpha", i/100)
            self.update()
            time.sleep(1/1000)

    def close(self):
        self.controller.upload_window = None
        self.fade_out()
        self.grab_release()
        self.destroy()