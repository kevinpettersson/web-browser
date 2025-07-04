import socket
import ssl
import html
from bs4 import BeautifulSoup # To parse html content when using the data scheme

class URL:
    open_sockets = {}
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
            s = self.get_socket()
            s.settimeout(10.0)

            request = self.create_http_request()
            
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

            #assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            # Handle status codes 3xx (Redirects)
            if 300 <= int(status) < 400:
                redirect = response_headers.get("location")
                if redirect is not None:
                    print(f"Redirecting to: {redirect}")
                    return self.handle_redirects(redirect, redirect_limit-1)

            # Handle reading of data  
            if response_headers.get("transfer-encoding") == "chunked":
                content = self.handle_transfer_encoding(response)
            elif "content-length" in response_headers:
                content_length = int(response_headers.get("content-length"))
                content = response.read(content_length)
            else:
                s.settimeout(10.0)
                content = response.read()

            # Close socket if specified by header 
            if response_headers.get("connection") == "close":
                key = (self.host, self.port)
                if key in URL.open_sockets:
                    del URL.open_sockets[key]
                s.close()

            return content
    
    def handle_transfer_encoding(self, response):
        body = ""
        while True:
            line = response.readline()
            chunk_size = int(line.strip(), 16)
            if chunk_size == 0:
                break
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
            "Connection": "close",
        }

        for key,value in headers.items():
            request += f"{key}: {value}\r\n"
        request += "\r\n"

        return request
        
    
def show(body, view_source=False):

    if(view_source):
        print(body, end="")
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
        print(decoded_text, end="")    


def load(url):
    body = url.request()
    show(body, url.is_view_source)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1]:  # Check if URL is not empty
        url = sys.argv[1]
    else:
        url = "file:///home/kevinpe/Documents/web-browser/homepage.html"
    load(URL(url))
        
