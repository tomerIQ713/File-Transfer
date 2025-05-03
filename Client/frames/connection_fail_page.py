from customtkinter import *

from utils import Colors, FONT

class ConnectionFailPage(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color=Colors.gray_20)

        CTkLabel(self, text='Failed to connect to Server', font=(FONT, 40)).pack()