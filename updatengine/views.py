from django.http import JsonResponse
import json
import os
from .utils import get_latest_release_version
from django.contrib.auth.views import PasswordChangeView
from django.http import Http404


def check_version(request):
    try:
        json_file = os.path.join(os.path.dirname(__file__), 'static/json/app.json')
        json_data = open(json_file).read()
        json_list = json.loads(json_data)
        repository = json_list['repository']
        url = 'https://github.com/' + repository
        url_release = 'https://api.github.com/repos/' + repository + '/releases'
        version = get_latest_release_version(url_release)
        data = {
            'version' : version,
            'url' : url + '/releases/tag/' + version,
        }
        return JsonResponse(data)
    except:
        return JsonResponse({
            'version' : '',
            'url' : ''
        })


class ChangePasswordView(PasswordChangeView):
    def get(self, *args, **kwargs):
        if self.request.user.userauth.ldap_auth:
            raise Http404
        return super(ChangePasswordView, self).get(*args, **kwargs)
