import urllib.parse
import time
import config
from mako.lookup import TemplateLookup
import security.authholder as authholder

__all__ = ['merge', 'render']

lookup = TemplateLookup(directories=[config.install_path + '/template'], input_encoding=config.encoding)

referer_key = 'referer'

def merge(template, data, request):
    template = lookup.get_template(template)
    data = data if data else {}
    if not 'config' in data:
        data['config'] = config
    if not 'login_redirect' in data:
        login_redirect = '' 
        if 'get' == request.get_method().lower():
            login_redirect = request.get_path()
            query_string = request.get_query_string()
            if query_string:
                login_redirect += '?' + query_string
        else:
            login_redirect = request.get_header(referer_key)
        login_redirect = urllib.parse.quote(login_redirect, encoding=request.get_encoding()) if login_redirect else ''
        data['login_redirect'] = login_redirect
    if not 'principal' in data:
        data['principal'] = authholder.principal()
    return template.render(**data)

def render(template, data, request, response):
    response.write(merge(template, data, request))