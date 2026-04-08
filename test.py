import re

with open('links.txt') as f: 
    links = f.read()
    url = (re.search("host:\s*(.*)", links)).group(1)

print(url)