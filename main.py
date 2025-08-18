from src.browser import Browser
from src.url import URL
from tkinter import *

if __name__ == "__main__":
    import sys
    browser = Browser()
    browser.new_tab(URL(sys.argv[1]))
    browser.window.mainloop()

    """    
    browser = Tab()
    browser.load(URL(url))    
    browser.window.mainloop()
    """