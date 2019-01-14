import urllib2
import re
    
def extract_text_from_url(url, regex):
    try:
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
        html = urllib2.urlopen(req).read()
        retval = re.search(regex, html, re.IGNORECASE | re.DOTALL).group(1)
    except:
        retval = ''
    return retval

