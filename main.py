from src.browser import Browser
from src.url import URL
from tkinter import *

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1]: 
        url = sys.argv[1]
    else:
        url = "file:///home/kevinpe/Documents/web-browser/homepage.html"
        
    browser = Browser()
    browser.load(URL(url))    
    browser.window.mainloop()