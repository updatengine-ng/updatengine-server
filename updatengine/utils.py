import urllib.request, urllib.error, urllib.parse
import json


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
