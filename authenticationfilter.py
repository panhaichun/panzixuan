import logging
import traceback
import urllib.parse
import config
import security.authholder as authholder
from security.authentication import AuthenticationProvider, AuthenticationException
import pzx.account as account
	
check_uri = '/check'

logout_uri = '/logout'

referer_key = 'referer'

redirect_key = 'redirect'

username_key = 'username'

password_key = 'password'

authentication_provider = AuthenticationProvider(account)

def authentication(pattern=None):
    def interceptor(func):
        def wrap(request, response):
            # 请求登录验证的
            if require_to_check(request):
                login(request, response)
                return
            # 获取认证对象
            authentication = get_authentication(request)
            #/ 注销
            if require_to_logout(request):
                logout(authentication, request, response)
                return;
            authholder.set(authentication)
            try:
                return func(request, response)
            finally:
                # 及时清除Thread变量，防止Thread重用带来bug
                authholder.set(None)
        return wrap
    return interceptor
	
def login(request, response):
    username = request.get_param(username_key)
    password = request.get_param(password_key)
    logging.info('用户[%s]请求系统认证' % username);
    try:
        authentication_provider.authenticate(username, password)
    except Exception as e:
        raise e
    # 认证失败统一由异常处理
    response.set_cookie(username_key, username, config.cookie_path, config.cookie_domain)
    response.set_cookie(password_key, password, config.cookie_path, config.cookie_domain)
    redirect = request.get_param(redirect_key)
    response.redirect(redirect if redirect else '/')
	
def get_authentication(request):
    cookies = request.get_cookies()
    username = cookies.get(username_key);
    if not username:
        return None
    password = cookies.get(password_key);
    try:
        #验证登录
        return authentication_provider.authenticate(username, password)
    except AuthenticationException as e:
        logging.warn(e)
        traceback.print_exc()
        return None

def logout(authentication, request, response):
    logging.info('用户[%s]请求注销' % str(authentication))
    try:
        authentication_provider.logout(authentication)
    except Exception as e:
        raise e
    response.set_cookie(username_key, '', config.cookie_path, config.cookie_domain)
    response.set_cookie(password_key, '', config.cookie_path, config.cookie_domain)
    response.redirect(request.get_header(referer_key, '/'))

def require_to_logout(request):
    return request.get_path().startswith(logout_uri)
    
def require_to_check(request):
    return request.get_path().startswith(check_uri)
    