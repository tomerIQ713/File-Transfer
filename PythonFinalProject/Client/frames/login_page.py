from customtkinter import *
from CTkMessagebox import CTkMessagebox

from utils import colors

class LoginPage(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color=colors['gray_20'])

        CTkLabel(self, text='Login / Signup', font=('Arial', 70)).place(in_=self, anchor=N, relx=0.5, y=60)

        self.username_entry = CTkEntry(self, width=420, height=50, corner_radius=0, border_width=0, font=('Arial', 20),
                                       fg_color=colors['gray_32'], text_color=colors['white'],
                                       placeholder_text='Enter username', placeholder_text_color=colors['gray_52'])
        self.username_entry.place(in_=self, anchor=N, relx=0.5, y=180)

        self.password_entry = CTkEntry(self, width=420, height=50, corner_radius=0, border_width=0, font=('Arial', 20),
                                       fg_color=colors['gray_32'], text_color=colors['white'],
                                       placeholder_text='Enter password', placeholder_text_color=colors['gray_52'])
        self.password_entry.place(in_=self, anchor=N, relx=0.5, y=270)

        self.login_button = CTkButton(self, width=150, height=60, text='Login', font=('Arial', 20),
                                      fg_color=colors['blue'], hover_color=colors['blue_hover'], border_width=0,
                                      command=self.login_command)
        self.login_button.place(in_=self, anchor=N, relx=0.32, y=430)

        self.signup_button = CTkButton(self, width=150, height=60, text='Signup', font=('Arial', 20),
                                      fg_color=colors['blue'], hover_color=colors['blue_hover'], border_width=0,
                                      command=self.signup_command)
        self.signup_button.place(in_=self, anchor=N, relx=0.68 , y=430)

    def login_command(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        response = self.controller.login(username, password)
        if not response[0]:
            self.show_message_box('Couldn\'t Log In', response[1], 'cancel')

    def signup_command(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        passed, response = self.controller.signup(username, password)
        if passed:
            self.show_message_box('Signup Successful', response, 'check')
        else:
            self.show_message_box('Couldn\'t Sign Up', response, 'cancel')

    def show_message_box(self, title: str, message: str, icon: str):
        CTkMessagebox(self, title=title, message=message,
                      icon=icon).get()