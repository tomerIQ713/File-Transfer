from customtkinter import *
from CTkMessagebox import CTkMessagebox

from utils import Colors, FONT

class LoginPage(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color=Colors.gray_20)

        CTkLabel(self, text='Login / Signup', font=('Roboto Slab Regular', 70)).pack(pady=(75, 35))

        self.username_entry = CTkEntry(self, width=420, height=50, border_width=0, font=(FONT, 20),
                                       fg_color=Colors.gray_32, text_color=Colors.gray_92,
                                       placeholder_text='Enter username', placeholder_text_color=Colors.gray_52)
        self.username_entry.pack(pady=15)

        password_frame = CTkFrame(self, fg_color='transparent')
        password_frame.pack(pady=15)
        self.password_entry = CTkEntry(password_frame, width=420, height=50, border_width=0, font=(FONT, 20),
                                       fg_color=Colors.gray_32, text_color=Colors.gray_92, show='*',
                                       placeholder_text='Enter password', placeholder_text_color=Colors.gray_52)
        self.password_entry.pack(pady=(0, 5))

        self.show_password = CTkCheckBox(password_frame, text='Show Password', font=(FONT, 16), width=10, height=10,
                                         border_color=Colors.gray_72, hover_color=Colors.gray_72,
                                         checkmark_color=Colors.gray_28, fg_color=Colors.gray_72,
                                         command=self.toggle_password_show)
        self.show_password.pack(anchor=W)

        buttons_frame = CTkFrame(self, fg_color='transparent')
        buttons_frame.pack(pady=25)
        self.login_button = CTkButton(buttons_frame, width=170, height=60, text='Login', font=(FONT, 28),
                                      fg_color=Colors.blue, hover_color=Colors.blue_hover, border_width=0,
                                      command=self.login_command)
        self.login_button.pack(padx=20, side=LEFT)

        self.signup_button = CTkButton(buttons_frame, width=170, height=60, text='Signup', font=(FONT, 28),
                                      fg_color=Colors.blue, hover_color=Colors.blue_hover, border_width=0,
                                      command=self.signup_command)
        self.signup_button.pack(padx=20, side=LEFT)

    def toggle_password_show(self):
        if self.show_password.get():
            self.password_entry.configure(show='')
        else:
            self.password_entry.configure(show='*')

    def login_command(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        accepted, response = self.controller.login(username, password)
        if not accepted:
            self.controller.show_message_box('Login Denied', response, 'cancel')

    def signup_command(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        accepted, response = self.controller.signup(username, password)
        if not accepted:
            self.controller.show_message_box('Signup Denied', response, 'cancel')