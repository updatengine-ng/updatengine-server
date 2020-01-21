import urllib.request, urllib.error, urllib.parse
import re
    
def extract_text_from_url(url, regex):
    try:
        req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"})
        html = urllib.request.urlopen(req).read()
        retval = re.search(regex, html, re.IGNORECASE | re.DOTALL).group(1)
    except:
        retval = ''
    return retval

