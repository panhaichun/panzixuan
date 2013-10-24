import ctrl.home, ctrl.login, ctrl.blog, ctrl.profile, ctrl.user, ctrl.group
import exceptionfilter, authenticationfilter

DISP_METHOD = 'dispatch'

def get_handler(path):
    if path == '/':
        return ctrl.home
    if path == '/login':
        return ctrl.login
    if path == '/blog':
        return ctrl.blog
    if path.startswith('/profile'):
        return ctrl.profile
    if path.startswith('/user'):
        return ctrl.user
    if path.startswith('/group'):
        return ctrl.group
    return None

@exceptionfilter.exception()
@authenticationfilter.authentication()
def dispatch(request, response):
    handler = get_handler(request.get_path())
    if not handler:
        raise exceptionfilter.NoHandlerFoundException
    callable = None
    if hasattr(handler, DISP_METHOD):
        disp = getattr(handler, DISP_METHOD)
        if hasattr(disp, '__call__'):
            callable = disp(request)
    if not callable or not hasattr(callable, '__call__'):
        method = request.get_method().lower()
        if hasattr(handler, method):
            callable = getattr(handler, method)
    if not callable or not hasattr(callable, '__call__'):
        raise exceptionfilter.NoMethodFoundException
    callable(request, response)
    