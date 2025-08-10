class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.attributes = attributes
        self.parent = parent
    
    def __repr__(self):
        return "<" + self.tag + ">"