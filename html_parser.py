from text import Text
from element import Element

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
    ]

class HTMLParser:
    def __init__(self, body, is_view_source):
        self.body = body
        self.unfinished = []
        self.is_view_source = is_view_source

    def finish(self):
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self   .unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def add_text(self, text):
        if text.isspace(): return
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)

        if tag.startswith("!"): return

        if tag.startswith("/"):
            if len(self.unfinished) == 1: 
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)

        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            if parent:
                parent.children.append(node)

        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)
    
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}

        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                # strip value off leading and ending quotations.
                if len(value) > 2 and value[0] in ["'", "\""] and value[-1] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""

        return tag, attributes

    def parse(self):
        if self.is_view_source:
            return Text(self.body)
        else:
            text = ""
            in_tag = False

            for c in self.body:
                if c == "<":
                    in_tag = True
                    if text: self.add_text(text)
                    text = ""
                elif c == ">":
                    in_tag = False
                    self.add_tag(text)
                    text = ""
                else:
                    text += c
            if not in_tag and text:
                self.add_text(text)
        return self.finish()
    
def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)