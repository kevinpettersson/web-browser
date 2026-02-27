# Super simplified web browser 

## Supports the following:
* Client-server connection over IP/TCP  
* Supports URL schemes such as http, https, data, file, and view-source.  
* HTTP response caching, redirects.  
* GUI with scrolling and resizing.
* Basic HTML parser
* Basic CSS parser

## How to run the application: 

### Step 1: Navigate to project folder
```
cd /path/to/web-browser  
```

### Step 2: (Recommended) Create and activate a virtual enviroment
``` 
python3 -m venv venv
```
```
source /venv/bin/activate 
```

### Step 3: Install the dependencies
```
pip install -r requirements.txt  
```

### Step 4: Run the application
```
python3 main.py https://example.com
```
