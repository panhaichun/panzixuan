import webutil

def get(request, response):
    webutil.render('/blog/index.html', {'subtitle': '日志'}, request, response)
    