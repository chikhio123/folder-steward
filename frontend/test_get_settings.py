import urllib.request
import json
print(urllib.request.urlopen('http://localhost:8000/api/settings').read().decode())
