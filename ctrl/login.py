import urllib.parse
import webutil

def get(request, response):
    webutil.render(
        '/login.html', 
        {'message': request.get_param('message'), 'redirect': urllib.parse.quote(request.get_param('redirect', request.get_header('referer', '/')), encoding=request.get_encoding())}, 
        request, 
        response)
    
