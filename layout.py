import tkinter.font
from text import Text
from element import Element
from draw import DrawRect, DrawText

HSTEP, VSTEP = 13, 18
FONTS = {}
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]

class BlockLayout:

    def __init__(self, node, parent, previous, width):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

        self.x = None
        self.y = None
        self.width = width
        self.height = None

        self.display_list = []

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
            self.layout_intermediate()
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12
            self.layout_width_cache = {}
            self.line = []
            self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()
            self.display_list.extend(child.display_list)

        if mode == "block":
            self.height = sum([
                child.height for child in self.children])
        else:
            self.height = self.cursor_y

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
    
    def get_width(self, word, font):
        if word not in self.layout_width_cache:
            self.layout_width_cache[word] = font.measure(word)

        return self.layout_width_cache[word]  

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        width = self.get_width(word, font)
        
        if self.cursor_x + width >= self.width:
            self.flush()
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += width + font.measure(" ")

    def flush(self):
        if not self.line: return

        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for rel_x, word, font in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_x = 0
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def paint(self):
        cmds = []
        if self.layout_mode() == "inline":
            if isinstance(self.node, Element) and self.node.tag == "pre":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, "gray")
                cmds.append(rect)
            for x, y, word, font in self.display_list:
                cmds.append(DrawText(x, y, word, font))
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

        child = BlockLayout(self.node, self, None, self.layout_width)
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