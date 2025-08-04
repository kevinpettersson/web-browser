import tkinter.font
from text import Text

HSTEP, VSTEP = 13, 18
FONTS = {}

class Layout:
    def __init__(self, tokens, width):
        self.layout_width = width
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.display_list = []
        self.line = []

        self.font = tkinter.font.Font()
        self.space_width = self.font.measure(" ")
        self.linespace = self.font.metrics("linespace") * 1.25
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.width_cache = {}
        
        self.recurse(tokens)

        self.flush()

    def recurse(self, tree):
        if tree is None: return

        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else: 
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
    
    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.cursor_y += VSTEP
            self.flush()

    def get_font(self, size, weight, style):
        key = (size, weight, style)
        if key not in FONTS:
            font = tkinter.font.Font(size=size, weight=weight, slant=style)
            label = tkinter.Label(font=font)
            FONTS[key] = (font, label)
        return FONTS[key][0]
    
    def get_width(self, word, font):
        if word not in self.width_cache:
            self.width_cache[word] = font.measure(word)

        return self.width_cache[word]  

    def word(self, word):
        font = self.get_font(self.size, self.weight, self.style)
        width = self.get_width(word, font)
        
        if self.cursor_x + width >= self.layout_width - HSTEP:
            self.flush()
            self.cursor_y += self.linespace
            self.cursor_x = HSTEP
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += width + self.space_width

    def flush(self):
        if not self.line: 
            return
        
        max_ascent = max([font.metrics("ascent") for _, _, font in self.line])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([font.metrics("descent") for _, _, font in self.line])
        self.cursor_y = baseline + 1.25 * max_descent # Save the new y value for the next line so it dosent collide with the line prior
        self.cursor_x = HSTEP
        self.line = []