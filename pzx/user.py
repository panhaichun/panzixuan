import time

from pzx.db import db_template
from pzx.pagination import Pagination
import security.encrypt
import pzx.group
import pzx.role

class User:

    ADMIN_USERNAME = 'admin'

    def __init__(self, id=None, username=None, password=None, name=None):
        self.id = id
        self.username = username
        self.password = password
        self.name = name
        self.groups = set()
        self.roles = set()
    
    def get_belong_groups(self):
        results = set()
        [results.update(self.__get_belong_groups(group)) for group in self.groups]
        return results
    
    def __get_belong_groups(self, group):
        groups = set()
        if group.parent:
            groups.update(self.__get_belong_groups(group.parent))
        groups.add(group)
        return groups

    def add_role(self, role):
        self.roles.add(role)
    
    def remove_role(self, role):
        self.roles.remove(role)
        
    def get_contain_roles(self):
        roles = self.roles.copy()
        [roles.update(group.get_contain_roles()) for group in self.groups]
        return roles
        
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.id == obj.id if isinstance(obj, User) else False

    def __hash__(self):
        return hash(self.id) if self.id else hash(self)
        
    def __str__(self):
        return 'User [username=%s, name=%s]' % (self.username, self.name)
        
class UserNotFoundException(Exception):
    pass
class IncompleteUserException(Exception):
    pass
class DuplicateUsernameException(Exception):
    pass
class PasswordVerifyException(Exception):
    pass

encryptor = security.encrypt.DEFAULT_ENCRYPTOR

def create(username, password, name):
    if not username or len(username) < 3 or len(username) > 16:
        raise IncompleteUserException('用户名不能为空，由3到16个字符组成')
    if not name or len(name) > 32:
        raise IncompleteUserException('姓名不能为空, 且长度不能超过32个字符')
    if password and len(password) > 16:
        raise IncompleteUserException('密码长度不能超过16个字符')
    if __repo_get_by_username(username):
        raise DuplicateUsernameException('用户名[%s]已存在' % username)
    user = User(None, username, encryptor.encrypt(password), name)
    __repo_save(user)
    return user

def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    user = __repo_get(id)
    if not user:
        raise UserNotFoundException('用户ID[%d]不存在' % id)
    return user

def get_by_username(username):
    if not username:
        raise ValueError('参数[username]不能为空')
    user = __repo_get_by_username(username);
    if not user:
        raise UserNotFoundException('用户名[%s]不存在' % username)
    return user

def find(keyword, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    total = __repo_count(keyword)
    start = (number - 1) * size
    return Pagination(number, size, total, __repo_find(keyword, start, size)) if total > start else Pagination(number, size, 0, [])

def update(id, name):
    if not id:
        raise ValueError('参数[id]不能为空')
    if not name or len(name) > 32:
        raise IncompleteUserException('姓名不能为空，且长度不能超过32个字符')
    user = get(id)
    user.name = name
    __repo_update(user)
    return user
    
def update_password(id, password):
    if not id:
        raise ValueError('参数[id]不能为空')
    if password and len(password) > 16:
        raise IncompleteUserException('密码长度不能超过16个字符')
    user = get(id)
    user.password = encryptor.encrypt(password)
    __repo_update(user)
    return user
    
def delete(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]不允许删除' % user.ADMIN_USERNAME)
    __repo_delete(user)
    
def get_self(id):
    return get(id)

def update_self(id, name):
    return update(id, name)
    
def update_self_password(id, password, original_password):
    user = get_self(id)
    if not __match(user.password, encryptor.encrypt(original_password)):
        raise PasswordVerifyException('原密码不匹配')
    return update_password(id, password)
    
def __match(src, request):
    return src == request if src or request else True
    
def set_groups(id, group_ids):
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]组不允许修改' % user.ADMIN_USERNAME)
    user.groups = set()
    if group_ids:
        user.groups.update([pzx.group.get(group_id) for group_id in group_ids])
    __repo_update(user)

def set_roles(id, role_ids):
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]角色不允许修改' % user.ADMIN_USERNAME)
    user.roles = set()
    if role_ids:
        user.roles.update([pzx.role.get(role_id) for role_id in role_ids])
    __repo_update(user)

def __map(data):
    user = User(data[0], data[1], data[2], data[3])
    user.groups.update(pzx.group.list_by_user(user.id))
    user.roles.update(pzx.role.list_by_user(user.id))
    return user
    
def __repo_save(user):
    user.id = db_template.insert('insert into T_USER (USERNAME, PASSWORD, NAME) VALUES (?, ?, ?)', (user.username, user.password, user.name))

def __repo_get(id):
    return db_template.query_object('select ID, USERNAME, PASSWORD, NAME from T_USER where ID = ?', (id,), __map)
    
def __repo_get_by_username(username):
    return db_template.query_object('select ID, USERNAME, PASSWORD, NAME from T_USER where USERNAME = ?', (username,), __map)

def __repo_count(keyword):
    sql = 'select count(*) from T_USER where 1 = 1'
    params = []
    if keyword:
        sql += ' and (USERNAME like ? or NAME like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    return db_template.query_object(sql, params)

def __repo_find(keyword, start, count):
    sql = 'select ID, USERNAME, PASSWORD, NAME from T_USER where 1 = 1'
    params = []
    if keyword:
        sql += ' and (USERNAME like ? or NAME like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    sql += ' order by ID desc limit ?, ?'
    params.extend((start, count))
    return db_template.query_list(sql, params, __map)

def __repo_update(user):
    db_template.update('update T_USER set USERNAME = ?, PASSWORD = ?, NAME = ? where ID = ?', (user.username, user.password, user.name, user.id))
    db_template.update('delete from T_USER_GROUP where USER_ID = ?', (user.id,))
    if user.groups:
        [db_template.insert('insert into T_USER_GROUP (USER_ID, GROUP_ID) values (?, ?)', (user.id, group.id)) for group in user.groups]
    db_template.update('delete from T_USER_ROLE where USER_ID = ?', (user.id,))
    if user.roles:
        [db_template.insert('insert into T_USER_ROLE (USER_ID, ROLE_ID) values (?, ?)', (user.id, role.id)) for role in user.roles]

def __repo_delete(user):
    db_template.update('delete from T_USER_ROLE where USER_ID = ?', (user.id,))
    db_template.update('delete from T_USER_GROUP where USER_ID = ?', (user.id,))
    db_template.update('delete from T_USER where ID = ?', (user.id,))
