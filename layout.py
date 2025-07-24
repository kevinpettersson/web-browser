import tkinter.font

HSTEP, VSTEP = 13, 18

class Layout:
    def __init__(self, tokens):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.display_list = []

        self.font = tkinter.font.Font()
        self.space_width = self.font.measure(" ")
        self.linespace = self.font.metrics("linespace") * 1.25
        self.weight = "normal"
        self.style = "roman"

    def layout(self, tokens):
        pass
