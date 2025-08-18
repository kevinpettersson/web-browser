from tkinter import *
from tkinter import ttk
import emoji
import os
from PIL import Image, ImageTk
from .layout import DocumentLayout, paint_tree
from .html_parser import HTMLParser
from .css_parser import CSSParser,style, tree_to_list
from .element import Element
from .tag_selector import cascade_priority

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 50

class Tab:

    def __init__(self, parent_width, parent_height):
        self.width = parent_width
        self.height = parent_height
        
        self.emoji_cache = {}
        self.rules = []
        self.DEFAULT_STYLE_SHEET = CSSParser(open("browser.css").read()).parse()

        self.url = None

    def total_height(self):
        if self.display_list:
            return self.display_list[-1].top + VSTEP
        return self.height

    #def on_scrollbar(self, *args):
    #    self.canvas.yview(*args)
    
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
        self.url = url
        body = url.request()
        self.nodes = HTMLParser(body, url.is_view_source).parse()

        # 1. Copy over the browsers default style-sheet
        #self.rules = self.DEFAULT_STYLE_SHEET.copy()
        self.rules = self.DEFAULT_STYLE_SHEET.copy()
        # 2. Find and load external stylesheets
        links = [node.attributes["href"]
            for node in tree_to_list(self.nodes, [])
            if isinstance(node, Element) 
            and node.tag == "link"
            and node.attributes.get("rel") == "stylesheet"
            and "href" in node.attributes]
        
        # 3. For each link, resolve the CSS rule and append it to rules
        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:
                continue
            self.rules.extend(CSSParser(body).parse())

        # 4. Apply all the CSS rules (default + external) to the DOM 
        style(self.nodes, sorted(self.rules, key=cascade_priority)) #store style information to each node

        self.document = DocumentLayout(self.nodes, self.width) # create DocumentLayout object, is parent to all BlockLayout's
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)
        
        self.canvas.delete("all")

        for cmd in self.display_list:
            cmd.execute(0, self.canvas)  

    def draw(self, canvas):
        canvas.config(scrollregion=(0, 0, self.width, self.total_height()))

    def scrollup(self):
        first,_ = self.canvas.yview()

        if first > 0.0:
            self.canvas.yview_scroll(-1, "units") 
    
    def scrolldown(self):
        self.canvas.yview_scroll(1, "units")

    def resize(self, width, height):

        self.canvas.config(width=width, height=height)
        
        self.document = DocumentLayout(self.nodes, width)
        self.document.layout()
        self.display_list = []
        paint_tree(self.document, self.display_list)

        self.canvas.delete("all")
        for cmd in self.display_list:
            cmd.execute(0, self.canvas)
        self.draw()
    
    def click(self, x, y):
        y += self.canvas.canvasy(0)

        objs = [obj for obj in tree_to_list(self.document, [])
                    if obj.x <= x < obj.x + obj.width
                    and obj.y <= y < obj.y + obj.height]
        
        if not objs:
            return 
        
        elt = objs[-1].node

        while elt:
            if not hasattr(elt, "tag"): 
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = self.url.resolve(elt.attributes["href"])
                return self.load(url)

            elt = elt.parent
