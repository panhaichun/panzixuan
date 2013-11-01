import urllib.parse
import webutil

def get(request, response):
    webutil.render(
        '/login.html', 
        {'message': request.get_param('message'), 'redirect': request.get_param('redirect', request.get_header('referer', ''))}, 
        request, 
        response)
