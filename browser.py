from tkinter import *
from tkinter import ttk
import emoji
import os
from PIL import Image, ImageTk
from text import Text
from tag import Tag
from layout import Layout

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 50

class Browser:

    def __init__(self):
        self.window = Tk()
        self.window.geometry(f"{WIDTH}x{HEIGHT}")

        self.tokens = None
        self.display_list = []

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
            width=WIDTH,
            height=HEIGHT,
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
            return self.display_list[-1][1] + VSTEP
        return HEIGHT

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
        self.tokens = lex(body, url.is_view_source)
        self.display_list = Layout(self.tokens, WIDTH).display_list
        self.draw()
    
    def draw(self):
        self.canvas.delete("all")
        scroll_y = self.canvas.canvasy(0)
        for x, y, c, f in self.display_list:
            if y + VSTEP >= scroll_y and y <= scroll_y + HEIGHT:
                if emoji.is_emoji(c):
                    emoji_ = self.get_emoji(c)
                    self.canvas.create_image(x, y, image=emoji_, anchor="nw")
                else:
                    self.canvas.create_text(x, y, text=c, anchor="nw", font=f)
        self.canvas.config(scrollregion=(0, 0, WIDTH, self.total_height()))

    def scrollup(self, _):
        first,_ = self.canvas.yview()

        if first > 0.0:
            self.canvas.yview_scroll(-1, "units") 
    
    def scrolldown(self, _):
        self.canvas.yview_scroll(1, "units") 

    def resize(self, e):
        global WIDTH, HEIGHT
        WIDTH = e.width
        HEIGHT = e.height
        self.canvas.config(width=WIDTH, height=HEIGHT)
        self.display_list = Layout(self.tokens, WIDTH).display_list
        self.draw()

def lex(body, view_source=False):
    if view_source:
        return Text(body)
    else:
        out = []
        buffer = ""
        in_tag = False

        for c in body:
            if c == "<":
                in_tag = True
                if buffer: out.append(Text(buffer))
                buffer = ""
            elif c == ">":
                in_tag = False
                out.append(Tag(buffer))
                buffer = ""
            else:
                buffer += c
        if not in_tag and buffer:
            out.append(Text(buffer))
                
        return out