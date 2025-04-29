from customtkinter import *

from utils import colors

class ConnectionFailedFrame(CTkFrame):
    def __init__(self, parent, controller, *args, **kwargs):
        CTkFrame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(fg_color=colors['gray_20'])

        CTkLabel(self, text='Failed to connect to Server', font=('Arial', 40)).place(in_=self, anchor=CENTER, x=338, y=250)