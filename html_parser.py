from text import Text
from element import Element

class HTMLParser:

    SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
    ]   

    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript", "link",
        "meta", "title", "style", "script",
    ]

    def __init__(self, body, is_view_source):
        self.body = body
        self.unfinished = []
        self.is_view_source = is_view_source

    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]

            if open_tags == [] and tag != "html":
                self.add_tag("html")

            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")

                else:
                    self.add_tag("body")

            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")

            else:
                break

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)

        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self   .unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)

        if tag.startswith("!"): return

        self.implicit_tags(tag)

        if tag.startswith("/"):
            if len(self.unfinished) == 1: 
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)

        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1] 
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
        if self.is_view_source: # return the whole html body as plain text
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