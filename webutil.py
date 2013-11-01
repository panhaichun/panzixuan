import urllib.parse
import time
import config
from mako.lookup import TemplateLookup
import security.authholder as authholder

__all__ = ['merge', 'render']

lookup = TemplateLookup(directories=[config.install_path + '/template'], input_encoding=config.encoding)

def merge(template, data, request):
    template = lookup.get_template(template)
    data = data if data else {}
    if not 'config' in data:
        data['config'] = config
    if not 'auth' in data:
        data['auth'] = authholder.get()
    return template.render(**data)

def render(template, data, request, response):
    response.write(merge(template, data, request))