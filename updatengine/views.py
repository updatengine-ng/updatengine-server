from django.http import JsonResponse
import json
import os
import ssl
from .utils import extract_text_from_url


def check_version(request):
    try:
        json_file = os.path.join(os.path.dirname(__file__), 'static/json/app.json')
        json_data = open(json_file).read()
        json_list = json.loads(json_data)
        # regex = 'releases/tag/(.+?)">'
        # version = extract_text_from_url(url, regex)
        repository = json_list['repository']
        url_release = 'https://api.github.com/repos/' + repository + '/releases'
        version = get_latest_release_version(url_release)
        data = {
            'version' : version,
            'url' : url + '/tag/' + version,
        }
        return JsonResponse(data)
    except:
        return JsonResponse({
            'version' : '',
            'url' : ''
        })

