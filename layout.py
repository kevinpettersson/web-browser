import tkinter.font
from text import Text

HSTEP, VSTEP = 13, 18

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
        
        for tok in tokens:
            self.token(tok)

        self.flush()

    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.cursor_y += VSTEP
            self.flush()


    def word(self, word):
        font = tkinter.font.Font(
            size = self.size,
            weight = self.weight,
            slant = self.style
        )
        if word not in self.width_cache:
            self.width_cache[word] = font.measure(word)

        width = self.width_cache[word]

        if self.cursor_x + width >= self.layout_width - HSTEP:
            self.flush()
            self.cursor_y += self.linespace
            self.cursor_x = HSTEP
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += width + self.space_width

    def flush(self):
        if not self.line: 
            return
        
        max_ascent = max([font.metrics("ascent") for x, word, font in self.line])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([font.metrics("descent") for x, word, font in self.line])
        self.cursor_y = baseline + 1.25 * max_descent # Save the new y value for the next line so it dosent collide with the line prior
        self.cursor_x = HSTEP
        self.line = []