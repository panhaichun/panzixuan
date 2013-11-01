import webutil

def get(request, response):
    webutil.render('/blog/index.html', {'title': '日志'}, request, response)
    