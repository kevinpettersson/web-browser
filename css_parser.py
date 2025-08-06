from element import Element

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
        if not (self.i < len(self.s)) and (self.s[self.i] == literal):
            raise Exception("Parsing error:Ooccurred while processing literal on line 23")

        self.i +=1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":") 
        self.whitespace()
        val = self.word()

        return prop.casefold(), val
    
    def body(self):
        pairs = {}

        while self.i < len(self.s):
            try: 
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                #if failing to parse a property value pair, skip until next semicolon.
                why = self.ignore_until([";"]) 
                if why == ";":
                    self.literal(":")
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
    
def style(node):
    node.style = {}
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()

        for property, value in pairs.items():
            node.style[property] = value 
        
    for child in node.children:
        style(child)
        


