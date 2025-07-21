# web-browser

### Simplified web browser which is currently in the works.
* Client-server connection over IP/TCP  
* Handles schemes such as http, https, data, file, and view-source.  
* HTML entities, response caching, redirects.  
* GUI which supports scrolling and resizing.

## How to run the application: 

### Step 1: Navigate to project folder
cd /path/to/web-browser  

### Step 2: (Recommended) Create and activate a virtual enviroment 
python3 -m venv venv
source /venv/bin/activate 

### Step 3: Install the dependencies
pip install -r requirements.txt  

### Step 4: Run the application
python3 browser.py http://example.com
