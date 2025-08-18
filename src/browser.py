
from tkinter import *
from tkinter import ttk
from .tab import Tab

SCROLL_STEP = 50

class Browser:
    def __init__(self):
        self.tabs = []
        self.active_tab = None

        self.window = Tk()
        self.width = 800
        self.height = 600
        self.window.geometry(f"{self.width}x{self.height}")

        self.frame = Frame(self.window)
        self.frame.pack(fill=BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.frame,
            orient=VERTICAL,
            command=self.on_scrollbar
        )
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.canvas = Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            yscrollincrement=SCROLL_STEP,
            bg="white",
        )
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-4>", self.handle_up)
        self.window.bind("<Button-5>", self.handle_down)
        self.window.bind("<Configure>", self.handle_resize)
        self.window.bind("<Button-1>", self.handle_click)

    def handle_click(self, e):
        self.active_tab.click(e.x, e.y, self.canvas)
        self.draw()
    
    def handle_down(self, _):
        self.active_tab.scrolldown(self.canvas)
        self.draw()
    
    def handle_up(self, _):
        self.active_tab.scrollup(self.canvas)
        self.draw()
    
    def handle_resize(self, _):
        for tab in self.tabs:
            tab.resize(self.width, self.height, self.canvas)
    
    def on_scrollbar(self, *args):
        self.canvas.yview(*args)
    
    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas)
    
    def new_tab(self, url):
        new_tab = Tab(self.width, self.height)
        new_tab.load(url, self.canvas)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()
