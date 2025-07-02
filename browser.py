import socket
import ssl
import html
from bs4 import BeautifulSoup # To parse html content when using the data scheme

class URL:
    def __init__(self, url):
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
        
    def request(self):
        if self.scheme == "file":
            # Handle file URLs - just read the local file
            try:
                with open(self.path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return f"Error: File not found: {self.path}"
            except Exception as e:
                return f"Error reading file: {e}"
            
        if self.scheme == "data":
            # Handle data URLs - display content to user
            if self.mediaType == "text/html":
                soup = BeautifulSoup(self.dataContent, "html.parser")
                return soup.prettify()
            elif self.mediaType == "text/plain":
                return self.dataContent
            else:
                return f"Unsupported media type: {self.mediaType}"
        
        # Handle HTTP/HTTPS URLs - use socket connection
        s = socket.socket(
            family=socket.AF_INET, 
            type=socket.SOCK_STREAM, 
            proto=socket.IPPROTO_TCP,
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = f"GET {self.path} HTTP/1.1\r\n"
        headers = {
            "Host": self.host,
            "User-Agent": "MyBrowser",
            "Connection": "close",
        }

        for key,value in headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"
        
        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explaination = statusline.split(" ", 2)
        response_headers = {}

        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip() 

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()
        return content
    
def show(body):
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
    print(decoded_text, end="")    


def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "file:///home/kevinpe/Documents/web-browser/homepage.html"
    load(URL(url))
        
