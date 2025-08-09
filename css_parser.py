from element import Element
from tag_selector import TagSelector, DescendantSelector

INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}

class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0
    
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%": #keep reading characters until we hit a whitepsace or #-.%
                self.i += 1
            else:
                break

        if not (self.i > start):
            raise Exception("Parsing error: Occured while processing word on line 18")
        return self.s[start:self.i] # return the sub-string read
    
    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception("Parsing error: Occurred while processing literal on line 23")

        self.i +=1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":") 
        self.whitespace()
        val = self.word()

        return prop.casefold(), val
    
    # Called when parsing property-value pairs for HTML or CSS
    def body(self):
        pairs = {}

        while self.i < len(self.s) and self.s[self.i] != "}":
            try: 
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                #if failing to parse a property value pair, skip until next semicolon(html) or closing bracket(css).
                why = self.ignore_until([";", "}"]) 
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                #end of the string
                    break 
        return pairs
    
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None
    
    def selector(self):
        out = TagSelector(self.word().casefold())
        self.whitespace()

        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        
        return out
    
    # Used to parse CSS rules (selector + property-value pairs)
    def parse(self):
        rules = []

        # moves through the string to parse the selector and when finding the 
        # opening bracket it will parse through the body of the prop, value pairs and finally append the rule to the list.
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules
    
def style(node, rules):
    node.style = {}
    for property, default_value in INHERITED_PROPERTIES.items():
        if node.parent:
            node.style[property] = node.parent.style[property]
        else:
            node.style[property] = default_value

    for selector, body in rules:
        if not selector.matches(node): 
            continue
        for property, value in body.items():
            node.style[property] = value

    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()

        for property, value in pairs.items():
            node.style[property] = value 
    
    if node.style["font-size"].endswith("%"):
        # all nodes inherit their parents font-size
        if node.parent:
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        # example: 120% --> remove trailing % then divide by 100 gives 1.2 
        node_pct = float(node.style["font-size"][:-1]) / 100
        # example: 16px --> remove trailing px gives 16.0
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"
        
    for child in node.children:
        style(child, rules)

def tree_to_list(tree, list):
    list.append(tree)

    for child in tree.children:
        tree_to_list(child, list)

    return list


        


