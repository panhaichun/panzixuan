import pzx.user
from security.authentication import AccountNotFoundException

class Account:
    '''
    表示一个用户账号
    '''
    def __init__(self, user):
        if not user:
            raise ValueError('参数[user]不能为空')
        self.__user = user
    
    def get_name(self):
        return self.__user.username
        
    def get_password(self):
        return self.__user.password

    def get_roles(self):
        roles = set()
        roles.update([role.name for role in self.__user.get_contain_roles()])
        return roles

    def get_prototype(self):
        return self.__user
    
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.__user == obj.get_prototype() if isinstance(obj, Account) else False

    def __hash__(self):
        return hash(self.__user)
        
    def __str__(self):
        return str(self.__user)

def find_account(name):
    try:
        return Account(pzx.user.get_by_username(name))
    except pzx.user.UserNotFoundException:
        raise AccountNotFoundException('账号[%s]不存在' % name)
