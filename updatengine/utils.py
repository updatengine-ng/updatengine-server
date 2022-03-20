import urllib.request, urllib.error, urllib.parse
import re
import json

def extract_text_from_url(url, regex):
    try:
        req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"})
        html = urllib.request.urlopen(req).read().decode("utf-8")
        retval = re.search(regex, html, re.IGNORECASE | re.DOTALL).group(1)
    except:
        retval = ''
    return retval

def get_latest_release_version(url):
    try:
        headers = {'User-Agent': "Magic Browser", 'Accept': "application/vnd.github.v3+json"}
        req = urllib.request.Request(url, headers= headers)
        html = urllib.request.urlopen(req).read().decode("utf-8")
        releases = json.loads(html)
        retval = releases[0]['tag_name']
    except Exception as e:
        retval = str(e)                                                                                                                                                                                                                       
    return retval

