import logging
import urllib.parse
import traceback

import security.authholder as authholder
from security.authentication import AuthenticationException
from security.authorization import AuthorizationException, UnAuthenticationException
import webutil
	
referer_key = 'referer'
redirect_key = 'redirect'

class NoHandlerFoundException(Exception):
    pass
class NoMethodFoundException(Exception):
    pass
    
def exception(pattern=None):
    def interceptor(func):
        def wrap(request, response):
            try:
                return func(request, response)
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                handle(e, request, response)
        return wrap
    return interceptor

def handle(e, request, response):
    response.reset()
    response.set_content_type('text/html; charset=%s' % request.get_encoding())
    
    # 认证异常
    if isinstance(e, AuthenticationException):
        url = request.get_ctx_path() + '/login?message=' + urllib.parse.quote(str(e), encoding=request.get_encoding())
        redirect = request.get_param(redirect_key)
        url = url + '&redirect=' + urllib.parse.quote(redirect, encoding=request.get_encoding()) if redirect else url
        response.redirect(url)
        return
    
    # 未登录访问了受保护的页面，重定向到登录页面
    if isinstance(e, UnAuthenticationException):
        login_redirect = ''
        if 'get' == request.get_method().lower():
            login_redirect = request.get_path()
        else:
            login_redirect = request.get_header(referer_key)
        login_redirect = urllib.parse.quote(login_redirect, encoding=request.get_encoding()) if login_redirect else ''
        response.redirect(request.get_ctx_path() + '/login?redirect=' + login_redirect)
        return
    
    status = 500
    message = e
    # 找不到控制器
    if isinstance(e, NoHandlerFoundException):
        status = 404
        message = '您请求的资源[%s]不存在' % request.get_path()
        logging.error(message)
    
    # 不能处理对应的Http方法
    if isinstance(e, NoMethodFoundException):
        if request.get_method() in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT'):
            status = 405
        else:
            status = 501
        message = '资源[%s]不支持[%s]请求方法' % (request.get_path(), request.get_method())
        logging.error(message)
     
    if isinstance(e, AuthorizationException):
        status = 403
        
    # 输出错误页面
    webutil.render('/error.html', {'status': status, 'message': message}, request, response)
