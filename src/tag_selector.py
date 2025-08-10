from .element import Element

class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1
        
    def matches(self, node):
        return isinstance(node, Element) and self.tag.lower() == node.tag.lower()

class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = self.ancestor.priority + self.descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node): return False

        while node.parent:
            if self.ancestor.matches(node.parent): return True
            node = node.parent
        return False
    
def cascade_priority(rule):
    selector, body = rule
    return selector.priority
        
