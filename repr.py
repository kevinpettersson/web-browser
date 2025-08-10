from src.url import URL
from src.html_parser import HTMLParser, print_tree
import sys

if __name__ == "__main__":

    body = URL(sys.argv[1]).request()
    nodes = HTMLParser(body, None).parse()
    print_tree(nodes)