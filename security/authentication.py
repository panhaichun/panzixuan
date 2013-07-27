import logging
import security.encrypt

__all__ = ['BASIC_ROLE', 'Authentication', 
            'AuthenticationException', 'AccountException', 'AccountNotFoundException', 'CredentialException', 
            'AuthenticationProvider']

BASIC_ROLE = 'USER'

class Authentication:
    '''
    表示一个认证实体
    '''
    def __init__(self, principal):
        if principal is None:
            raise ValueError('参数[principal]不能为空')
        self.__principal = principal # 实际账户
        self.__roles = set([BASIC_ROLE])
        self.__roles.update(principal.get_roles())
        
    def get_name(self):
        return self.__principal.get_name()
        
    def get_roles(self):
        return self.__roles
        
    def get_principal(self):
        return self.__principal
        
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.__principal == obj.get_principal() if isinstance(obj, Authentication) else False
    
    def __hash__(self):
        return hash(self.__principal)
        
    def __str__(self):
        return str(self.__principal)

class AuthenticationException(Exception):
    pass
class AccountException(AuthenticationException):
    pass
class AccountNotFoundException(AuthenticationException):
    pass
class CredentialException(AuthenticationException):
    pass

class AuthenticationProvider:

    def __init__(self, account_service, encryptor=None):
        if account_service is None:
            raise ValueError('参数[account_service]不能为空')
        self.__account_service = account_service
        self.__encryptor = security.encrypt.DEFAULT_ENCRYPTOR if not encryptor else encryptor
        
    def authenticate(self, name, password):
        logging.info('认证用户[%s]' % name)
        if not name:
            raise AccountNotFoundException('帐号名不能为空')
        account = self.__account_service.find_account(name)
        req_password = self.__appropriate_encryptor(account).encrypt(password)
        if not self.__match(account.get_password(), req_password):
            raise CredentialException('帐号和密码不匹配')
        return Authentication(account)
    
    def __match(self, src, request):
        return src == request if src or request else True
    
    def __appropriate_encryptor(self, account):
        return self.__encryptor
        
    def logout(self, authentication):
        logging.info('注销用户[%s]' % str(authentication))
        if not authentication:
            logging.warn('用户未认证')
