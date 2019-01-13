from django.http import JsonResponse
import json
import urllib2
import re
import datetime

def check_version(request):
    urlFile = urllib2.urlopen(request.build_absolute_uri('/') + 'static/json/app.json',)
    jsonList = json.load(urlFile)
    url = jsonList['url'] + '/releases'
        
    regex = 'releases/tag/(.+?)">'
    version = extract_text_from_url(url, regex)

    data = {
        'version' : version,
        'url' : url + '/tag/' + version,
    }
    return JsonResponse(data)
    
def extract_text_from_url(url, regex):
    try:
        req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"})
        html = urllib2.urlopen(req).read()
        version = re.search(regex, html, re.IGNORECASE | re.DOTALL).group(1)
    except:
        version = ''
    return version
