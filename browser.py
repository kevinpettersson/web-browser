import html
from tkinter import *
from tkinter import ttk
import tkinter.font
import emoji
import os
from PIL import Image, ImageTk
from text import Text
from tag import Tag

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 50

class Browser:

    def __init__(self):
        self.window = Tk()
        self.window.geometry(f"{WIDTH}x{HEIGHT}")

        self.text=""
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
        cleaned_body = lex(body, url.is_view_source)
        self.text = cleaned_body
        self.display_list = layout(cleaned_body)
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
        self.canvas.yview_scroll(-1, "units") 
    
    def scrolldown(self, _):
        self.canvas.yview_scroll(1, "units") 

    def resize(self, e):
        global WIDTH, HEIGHT
        WIDTH = e.width
        HEIGHT = e.height
        self.canvas.config(width=WIDTH, height=HEIGHT)
        self.display_list = layout(self.text)
        self.draw()

def lex(body, view_source=False):
    if view_source:
        return body
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
                
        #decoded_text = html.unescape(out)
        return out

def layout(token):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    font = tkinter.font.Font()
    space_width = font.measure(" ")
    linespace = font.metrics("linespace") * 1.25
    weight = "normal"
    style = "roman"

    width_cache = {} # To optimize loading times when resizing window and pages with large amoutn fo text.

    for tok in token:
        if isinstance(tok, Text):
            for word in tok.text.split():
                font = tkinter.font.Font(
                    size = 16,
                    weight=weight,
                    slant=style
                )
                if word not in width_cache:
                    width_cache[word] = font.measure(word)

                width = width_cache[word]

                if cursor_x + width >= WIDTH - HSTEP:
                    cursor_y += linespace
                    cursor_x = HSTEP
                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += width + space_width

        elif tok.tag == "i":
            style = "italic"
        elif tok.tag == "/i":
            syle = "roman"
        elif tok.tag == "b":
            weight = "bold"
        elif style == "/b":
            style == "normal"

    return display_list