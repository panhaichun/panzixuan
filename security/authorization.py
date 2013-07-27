import logging
import security.authholder as authholder

__all__ = ['Resource', 'AuthorizationException', 'UnAuthenticationException', 'UnauthorizedException', 'AuthorizationProvider', 'protected']

class Resource(object):
    '''
    表示一个资源
    '''
    def __init__(self, path, name=None, allow_roles=None):
        self.__path = path
        self.__name = name
        self.__allow_roles = allow_roles if allow_roles else () # 该资源允许哪些角色访问，为空表示任何角色都能访问
        
    def get_path(self):
        return self.__path;

    def get_name(self):
        return self.__name;

    def allow_roles(self):
        return self.__allow_roles;
    
    def is_protected(self):
        return True if self.__allow_roles else False
        
    def match(self, path):
        return self.__path == path
    
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.__path == obj.get_path() if isinstance(obj, Resource) else False
    
    def __hash__(self):
        return hash(self.__path)
        
    def __str__(self):
        return 'Resource [path=%s, name=%s]' % (self.__path, self.__name)
        
class AuthorizationException(Exception):
    pass
class UnAuthenticationException(AuthorizationException):
    '''
    没有认证过的用户访问受保护的资源时抛出
    '''
    pass
class UnauthorizedException(AuthorizationException):
    '''
    用户没有访问权限时抛出
    '''
    pass

class AuthorizationProvider:
    
    def access(self, auth, resource, arguments):
        if resource.is_protected():
            if not auth:
                raise UnAuthenticationException('资源[%s]不允许匿名访问' % str(resource))
            if not self.__accessable(auth, set(resource.allow_roles())):
                raise UnauthorizedException('用户[%s]没有访问资源[%s]的权限' % (str(auth), str(resource)))
                
    def __accessable(self, auth, role_names):
        if not role_names:
            return True
        roles = auth.get_roles()
        if not roles:
            return False
        return role_names & roles
        
authorization_provider = AuthorizationProvider()
        
def protected(name=None, allow_roles=None):
    '''
    python提供的装饰功能，包装方法，在实际调用之前根据[name]和[allow_roles]参数进行权限判断
    '''
    def interceptor(func):
        def wrap(*args, **argkw):
            arguments = {}
            i = 0
            for arg in args:
                arguments['arg%d' % i] = arg
                i += 1
            arguments.update(argkw)
            authentication = authholder.get()
            resource = Resource(str(func), name, allow_roles)
            logging.debug('用户[%s]访问资源[%s], 提交参数[%s]' % (str(authentication), str(resource), str(arguments)))
            authorization_provider.access(authentication, resource, arguments)
            return func(*args, **argkw)
        return wrap
    return interceptor
    