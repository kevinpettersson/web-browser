import socket
import ssl
import html
import time
import gzip
from tkinter import *
from bs4 import BeautifulSoup # To parse html content when using the data scheme

class URL:
    open_sockets = {}
    response_cache = {}

    def __init__(self, url):
        self.is_view_source = False

        # Handle view-source scheme
        if url.startswith("view-source"):
            self.is_view_source = True
            url = url[len("view-source:"):] # Remove view-source prefix

        if "://" not in url: 
            self.scheme, url = url.split(":", 1)
        else: 
            self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file", "data"]

        if self.scheme == "file":
            # For file URLs - no host, no port, just file path
            self.host = None    
            self.port = None
            self.path = url 

        elif self.scheme == "data":
            # For data html/text URLs
            self.host = None
            self.port = None
            self.path = None
            self.mediaType, self.dataContent = url.split(",", 1)

        else: 
            # For HTTP/HTTPS URLs
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1)
            self.path = "/" + url
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
        
    def request(self, redirect_limit=5):
        if redirect_limit <= 0:
            return "Error: Too many redirects"
        
        if self.scheme == "file":
            return self.handle_file_request()
            
        elif self.scheme == "data":
            return self.handle_data_request()
        
        else:
            # Handling HTTP/HTTPS requests
            cache_key = str(self)
            cached = URL.response_cache.get(cache_key)

            if cached:
                if time.time() < cached["expires"]:
                    print("Returning cached content")
                    return cached["content"]
                else:
                    print("Time expired, removing cached object")
                    del URL.response_cache[cache_key]

            s = self.get_socket()
            s.settimeout(10.0)

            request = self.create_http_request()
            
            s.send(request.encode("utf8"))

            response = s.makefile("rb", newline=b"\r\n")
            statusline = response.readline().decode("utf-8")
            _, status, _ = statusline.split(" ", 2)
            response_headers = {}

            while True:
                line = response.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                header_line = line.decode("utf-8")
                header, value = header_line.split(":", 1)
                response_headers[header.casefold()] = value.strip() 

            # Handle status codes 3xx (Redirects)
            if 300 <= int(status) < 400:
                redirect = response_headers.get("location")
                if redirect is not None:
                    print(f"Redirecting to: {redirect}")
                    return self.handle_redirects(redirect, redirect_limit-1)

            # Handle reading of data (creating content) 
            if response_headers.get("transfer-encoding") == "chunked":
                content = self.handle_transfer_encoding(response)
            elif "content-length" in response_headers:
                content_length = int(response_headers.get("content-length"))
                content = response.read(content_length)
            else:
                s.settimeout(10.0)
                content = response.read()

            if response_headers.get("content-encoding", "").lower() == "gzip":
                try:
                    content = gzip.decompress(content)
                except Exception as e:
                    return f"Error decompressing gzip content: {e}"

            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        content = content.decode("iso-8859-1")  # Fallback to common legacy encoding
                    except Exception:
                        content = content.decode("utf-8", errors="replace")  # Last resort: replace bad characters

            # Handle caching for 200 OK responses
            cache_key = str(self)
            if int(status) == 200:
                max_age = self.should_cache(response_headers)
                if max_age:
                    URL.response_cache[cache_key] = {
                        "headers": response_headers,
                        "content": content,
                        "expires": time.time() + max_age,
                    }

            # Close socket if specified by header 
            if response_headers.get("connection") == "close":
                key = (self.host, self.port)
                if key in URL.open_sockets:
                    del URL.open_sockets[key]
                s.close()

            return content
    
    def should_cache(self, headers):
        cache_control = headers.get("cache-control")

        if not cache_control:
            return False
        
        cache_control = headers.get("cache-control").lower()
        if "no-store" in cache_control:
            return False
        
        if "no-cache" in cache_control:
            return False
        
        if "max-age" in cache_control:
            parts = cache_control.split(",")
            for part in parts:
                if "max-age" in part:
                    _, value = part.strip().split("=")
                    try:
                        age = int(value)
                        return age
                    except:
                        return False
        return False
    
    def handle_transfer_encoding(self, response):
        body = b""
        while True:
            line = response.readline()
            if not line:
                break
            chunk_size_str = line.strip().decode("utf-8")
            if not chunk_size_str:
                break
            chunk_size = int(chunk_size_str, 16)
            body += response.read(chunk_size)
            response.read(2)
        return body
        
    def handle_redirects(self, redirect, redirect_limit):
        key = (self.host, self.port)
        if key in URL.open_sockets:
            URL.open_sockets[key].close()
            del URL.open_sockets[key]

        if redirect.startswith("/"):
            redirect_url = f"{self.scheme}://{self.host}{redirect}"
        elif "://" not in redirect:
            redirect_url = f"{self.scheme}://{self.host}/{redirect}"
        else:
            redirect_url = redirect 
        print(f"Following redirect to: {redirect_url}")
        return URL(redirect_url).request(redirect_limit)
    
    def handle_file_request(self):
        # Handle file requests, just read the local file
        try:
            with open(self.path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {self.path}"
        except Exception as e:
            return f"Error reading file: {e}"
    
    def handle_data_request(self):
        # Handle data URLs - display content to user
        if self.mediaType == "text/html":
            soup = BeautifulSoup(self.dataContent, "html.parser")
            return soup.prettify()
        elif self.mediaType == "text/plain":
            return self.dataContent
        else:
            return f"Unsupported media type: {self.mediaType}"
    
    def get_socket(self):
        # Handle HTTP/HTTPS URLs - use socket connection
        key = (self.host, self.port)

        if key in URL.open_sockets:
            s = URL.open_sockets[key]
        else:
            s = socket.socket(
                family=socket.AF_INET, 
                type=socket.SOCK_STREAM, 
                proto=socket.IPPROTO_TCP,
            )
            
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            URL.open_sockets[key] = s

        return s

    def create_http_request(self):
        request = f"GET {self.path} HTTP/1.0\r\n"

        headers = {
            "Host": self.host,
            "User-Agent": "MyBrowser",
            "Accept-Encoding": "gzip",
        }

        for key,value in headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"

        return request

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 50

class Browser:

    def __init__(self):
        self.scroll = 0
        self.window = Tk()
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<Configure>", self.resize)
        self.scrollbar = Scrollbar(
            self.window,
            bg="black",
            troughcolor="grey")
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas = Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT,
        )
        self.canvas.pack(fill="both", expand=True)

    def load(self, url):
        body = url.request()
        cleaned_body = lex(body, url.is_view_source)
        self.text = cleaned_body # Store body inside instance variable for future use (resize).
        self.display_list = layout(cleaned_body)
        self.draw()
    
    def draw(self):
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrollup(self, e):
        if self.scroll - SCROLL_STEP >= 0:
            self.scroll -= SCROLL_STEP
            self.canvas.delete("all")
            self.draw()
    
    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.canvas.delete("all")
        self.draw()

    def resize(self, e):
        global WIDTH, HEIGHT
        WIDTH = e.width
        HEIGHT = e.height

        self.canvas.delete("all")
        self.display_list = layout(self.text)
        self.draw()
        
def lex(body, view_source=False):
    if view_source:
        return body
    else:
        in_tag = False
        text_only = ""

        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                text_only += c
                
        decoded_text = html.unescape(text_only)
        return decoded_text 

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    for c in text:
        if c == "\n":
            cursor_y += VSTEP
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP

    return display_list


if __name__ == "__main__":
    import sys
    #if len(sys.argv) > 1 and sys.argv[1]:  # Check if URL is not empty
    #    url = sys.argv[1]p>"
    #else:
    #    url = "file:///home/kevinpe/Documents/web-browser/homepage.html"
    #load(URL(url))
    Browser().load(URL(sys.argv[1]))
    mainloop()
        
