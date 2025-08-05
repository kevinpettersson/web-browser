from tkinter import *
from tkinter import ttk
import emoji
import os
from PIL import Image, ImageTk
from layout import DocumentLayout, paint_tree
from html_parser import HTMLParser

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 50

class Browser:

    def __init__(self):
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
            yscrollincrement=SCROLL_STEP
        )
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.canvas.config(yscrollcommand=self.scrollbar.set)

        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Configure>", self.resize)

        self.emoji_cache = {}

    def total_height(self):
        if self.display_list:
            return self.display_list[-1].top + VSTEP
        return self.height

    def on_scrollbar(self, *args):
        self.canvas.yview(*args)
    
    def get_emoji(self, char):
        filename = "-".join(f"{ord(c):x}" for c in char)
        filename = str.upper(filename)
        filename += ".png"

        path = os.path.join("OpenMoji", filename)

        if not os.path.exists(path):
            return None
        elif path not in self.emoji_cache: 
            image = Image.open(path)
            resized_image = image.resize((16, 16))
            img = ImageTk.PhotoImage(resized_image)
            self.emoji_cache[path] = img
        return self.emoji_cache[path]

    def load(self, url):
        body = url.request()
        self.nodes = HTMLParser(body, url.is_view_source).parse()
        self.document = DocumentLayout(self.nodes, self.width)

        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        
        self.canvas.delete("all")

        for cmd in self.display_list:
            cmd.execute(0, self.canvas)  

        self.draw()

    def draw(self):
        self.canvas.config(scrollregion=(0, 0, self.width, self.total_height()))


    def scrollup(self, _):
        first,_ = self.canvas.yview()

        if first > 0.0:
            self.canvas.yview_scroll(-1, "units") 
    
    def scrolldown(self, _):
        self.canvas.yview_scroll(1, "units")

    def resize(self, e):
        self.width = e.width
        self.height = e.height
        self.canvas.config(width=e.width, height=e.height)

        self.document = DocumentLayout(self.nodes, self.width)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)

        self.canvas.delete("all")
        for cmd in self.display_list:
            cmd.execute(0, self.canvas)
        self.draw()