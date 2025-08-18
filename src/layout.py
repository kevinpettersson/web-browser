import tkinter.font
from .text import Text
from .element import Element
from .draw import DrawRect, DrawText

HSTEP, VSTEP = 13, 18
FONTS = {}
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary",
]

class BlockLayout:

    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None

        self.display_list = []
        self.layout_width_cache = {}

    def recurse(self, node):
        if isinstance(node, Text):
            for word in node.text.split():
                self.word(node, word)
        else:
            if node.tag == "br":
                self.new_line()
            
            for child in node.children:
                self.recurse(child)
    
    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous, self.width)
            self.children.append(next)
            previous = next

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and child.tag in BLOCK_ELEMENTS for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"
    
    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.new_line()
            self.recurse(self.node)

        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])

    def get_width(self, word, font):
        if word not in self.layout_width_cache:
            self.layout_width_cache[word] = font.measure(word)

        return self.layout_width_cache[word]  

    def word(self, node, word):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        # font-style needs to be translated from CSS "normal" to Tk "roman"
        if style == "normal": style = "roman"
        # font-size needs to be translated from CSS pixels to Tk points 
        size = int(float(node.style["font-size"][:-2]) * 0.75)
        font = get_font(size, weight, style)

        width = self.get_width(word, font)
        if self.cursor_x + width >= self.width:
            self.new_line()
        line = self.children[-1]
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)
        self.cursor_x += width + font.measure(" ")
    
    def new_line(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def flush(self):
        if not self.line: return

        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font, color))

        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self):
        cmds = []
        if self.layout_mode() == "inline":

            if isinstance(self.node, Element): #and self.node.tag == "pre":
                bgcolor = self.node.style.get("background-color", "transparent")

                if bgcolor != "transparent":
                    x2, y2 = self.x + self.width, self.y + self.height
                    rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                    cmds.append(rect)

        return cmds

class DocumentLayout:
    def __init__(self, node, width):
        self.node = node
        self.parent = None
        self.children = []
        self.layout_width = width

    def layout(self):
        self.width = self.layout_width - (2 * HSTEP)
        self.x = HSTEP
        self.y = VSTEP

        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()

        self.height = child.height
    
    def paint(self):
        return []

def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)

def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]

class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
    
    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        for word in self.children:
            word.layout()
        
        if not self.children:
            self.height = 0
            return
        
        max_ascent = max([word.font.metrics("ascent") 
                            for word in self.children])
        max_descent = max([word.font.metrics("descent")
                            for word in self.children])

        baseline = self.y + 1.25 * max_ascent

        # deciding each word y-value that belongs to the line object.
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        
        self.height = 1.25 * (max_ascent + max_descent)
            
        
    def paint(self):
        return []

class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous
        self.children = []
    
    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        # font-style needs to be translated from CSS "normal" to Tk "roman"
        if style == "normal": style = "roman"
        # font-size needs to be translated from CSS pixels to Tk points 
        size = int(float(self.node.style["font-size"][:-2]) * 0.75)
        self.font = get_font(size, weight, style)

        self.width = self.font.measure(self.word)
        
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.y, self.word, self.font, color)]
        