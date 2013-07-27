from pzx.db import db_template
from pzx.pagination import Pagination
import security.encrypt

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
    
    def contains_role(self, role_name):
        return role_name in [role.name for role in self.get_contain_roles()]
        
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.id == obj.id if isinstance(obj, User) else False

    def __hash__(self):
        return hash(self.id) if self.id else hash(self)
        
    def __str__(self):
        return "User [username=%s, name=%s]" % (self.username, self.name)
        
class Group:

    ROOT_GROUP_NAME = '用户'
    
    ADMIN_GROUP_NAME = '管理员'
    
    def __init__(self, id=None, name=None, parent=None, description=None):
        self.id = id
        self.name = name
        self.parent = parent
        self.roles = set()
        self.description = description
        
    def add_role(self, role):
        self.roles.add(role)
        
    def remove_role(self, role):
        self.roles.remove(role)
        
    def get_contain_roles(self):
        roles = self.roles.copy()
        if self.parent:
            roles.update(self.parent.get_contain_roles())
        return roles
        
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.id == obj.id if isinstance(obj, Group) else False

    def __hash__(self):
        return hash(self.id) if self.id else hash(self)
        
    def __str__(self):
        return "Group [name=%s]" % self.name
        
class Role:
    
    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description
        
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.id == obj.id if isinstance(obj, Role) else False

    def __hash__(self):
        return hash(self.id) if self.id else hash(self)
        
    def __str__(self):
        return "Role [name=%s]" % self.name
        
class UserNotFoundException(Exception):
    pass
class IncompleteUserException(Exception):
    pass
class DuplicateUsernameException(Exception):
    pass
class PasswordVerifyException(Exception):
    pass
class GroupNotFoundException(Exception):
    pass
class IncompleteGroupException(Exception):
    pass
class DuplicateGroupNameException(Exception):
    pass
class GroupBeUsingException(Exception):
    pass
class RoleNotFoundException(Exception):
    pass

encryptor = security.encrypt.DEFAULT_ENCRYPTOR

def create(username, password, name):
    if not username or len(username) < 3 or len(username) > 16:
        raise IncompleteUserException('用户名不能为空，由3到16个字符组成')
    if not name or len(name) > 32:
        raise IncompleteUserException('姓名不能为空, 且长度不能超过32个字符')
    if password and len(password) > 16:
        raise IncompleteUserException('密码长度不能超过16个字符')
    if __db_get_by_username(username):
        raise DuplicateUsernameException('用户名[%s]已存在' % username)
    user = User(None, username, encryptor.encrypt(password), name)
    __db_save(user)
    return user

def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    user = __db_get(id)
    if not user:
        raise UserNotFoundException('用户id[%d]不存在' % id)
    return user

def get_by_username(username):
    if not username:
        raise ValueError('参数[username]不能为空')
    user = __db_get_by_username(username);
    if not user:
        raise UserNotFoundException('用户名[%s]不存在' % username)
    return user

def find(keyword, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    total = __db_count(keyword)
    start = (number - 1) * size
    return Pagination(number, size, total, __db_find(keyword, start, size)) if total > start else Pagination(number, size, 0, [])

def update(id, name):
    if not id:
        raise ValueError('参数[id]不能为空')
    if not name or len(name) > 32:
        raise IncompleteUserException('姓名不能为空，且长度不能超过32个字符')
    user = get(id)
    user.name = name
    __db_update(user)
    return user
    
def update_password(id, password):
    if not id:
        raise ValueError('参数[id]不能为空')
    if password and len(password) > 16:
        raise IncompleteUserException('密码长度不能超过16个字符')
    user = get(id)
    user.password = encryptor.encrypt(password)
    __db_update(user)
    return user
    
def delete(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]不允许删除' % user.ADMIN_USERNAME)
    __db_delete(user)
    
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
    
def create_group(name, description, parent_id):
    if not name or len(name) > 32:
        raise IncompleteGroupException('名称不能为空，且长度不能超过32个字符')
    if description and len(description) > 128:
        raise IncompleteGroupException('描述长度不能超过128个字符')
    parent = None
    if parent_id is None:
        parent = __db_get_root_group()
    else:
        try:
            parent = get_group(parent_id)
        except GroupNotFoundException:
            raise IncompleteGroupException('父组ID[%d]不存在' % parent_id)
    if __db_get_group_by_name(name):
        raise DuplicateGroupNameException('组名称[%s]已存在' % name)
    group = Group(None, name, parent, description)
    __db_save_group(group)
    return group
    
def get_group(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    group = __db_get_group(id)
    if not group:
        raise GroupNotFoundException('组ID[%s]不存在' % id)
    return group

def list_group():
    return __db_list_group()

def find_group(keyword, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    total = __db_count_group(keyword)
    start = (number - 1) * size
    return Pagination(number, size, total, __db_find_group(keyword, start, size)) if total > start else Pagination(number, size, 0, [])
    
def update_group(id, name, description):
    group = get_group(id)
    if not name or len(name) > 32:
        raise IncompleteGroupException('名称不能为空，且长度不能超过32个字符')
    if description and len(description) > 128:
        raise IncompleteGroupException('描述长度不能超过128个字符')
    another = __db_get_group_by_name(name)
    if another and not id == another.id:
        raise DuplicateGroupNameException('组名 [%s] 已存在' % name)
    if not name == group.name and group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]名称不允许修改' % group.name)
    group.name = name
    group.description = description
    __db_update_group(group)
    return group
    
def delete_group(id):
    group = get_group(id)
    if group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]不允许删除' % group.name)
    if __db_group_has_child(id):
        raise GroupBeUsingException('组[%d]包含子组, 不能删除' % id)
    if __db_group_be_using(id):
        raise GroupBeUsingException('组[%d]正在被用户使用, 不能删除' % id)
    __db_delete_group(group)

def get_role(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    role = __db_get_role(id)
    if not role:
        raise RoleNotFoundException('角色ID[%s]不存在' % id)
    return role

def list_role():
    return __db_list_role()
    
def set_groups(id, group_ids):
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]组不允许修改' % user.ADMIN_USERNAME)
    user.groups = set()
    if group_ids:
        user.groups.update([get_group(group_id) for group_id in group_ids])
    __db_update(user)

def set_roles(id, role_ids):
    user = get(id)
    if user.ADMIN_USERNAME == user.username:
        raise IncompleteUserException('用户[%s]角色不允许修改' % user.ADMIN_USERNAME)
    user.roles = set()
    if role_ids:
        user.roles.update([get_role(role_id) for role_id in role_ids])
    __db_update(user)

def set_group_roles(id, role_ids):
    group = get_group(id)
    if group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]角色不允许修改' % group.name)
    group.roles = set()
    if role_ids:
        group.roles.update([get_role(role_id) for role_id in role_ids])
    __db_update_group(group)

def __map_user(data):
    user = User(data[0], data[1], data[2], data[3])
    user.groups.update(__db_find_group_by_user(user.id))
    user.roles.update(__db_find_role_by_user(user.id))
    return user

def __map_group(data):
    group = Group(data[0], data[1], __db_get_group(data[2]) if data[2] else None, data[3])
    group.roles.update(__db_find_role_by_group(group.id))
    return group
    
def __map_role(data):
    return Role(data[0], data[1], data[2])
    
def __db_save(user):
    params = (user.username, user.password, user.name)
    user.id = db_template.insert('insert into T_USER (USERNAME, PASSWORD, NAME) VALUES (?, ?, ?)', params)

def __db_get(id):
    return db_template.query_object('select ID, USERNAME, PASSWORD, NAME from T_USER where ID = ?', (id,), __map_user)
    
def __db_get_by_username(username):
    return db_template.query_object('select ID, USERNAME, PASSWORD, NAME from T_USER where USERNAME = ?', (username,), __map_user)

def __db_count(keyword):
    sql = 'select count(*) from T_USER where 1 = 1'
    params = []
    if keyword:
        sql += ' and (USERNAME like ? or NAME like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    return db_template.query_object(sql, params)

def __db_find(keyword, start, count):
    sql = 'select ID, USERNAME, PASSWORD, NAME from T_USER where 1 = 1'
    params = []
    if keyword:
        sql += ' and (USERNAME like ? or NAME like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    sql += ' order by ID desc limit ?, ?'
    params.extend((start, count))
    return db_template.query_list(sql, params, __map_user)

def __db_update(user):
    db_template.update('update T_USER set USERNAME = ?, PASSWORD = ?, NAME = ? where ID = ?', (user.username, user.password, user.name, user.id))
    db_template.update('delete from T_USER_GROUP where USER_ID = ?', (user.id,))
    if user.groups:
        [db_template.insert('insert into T_USER_GROUP (USER_ID, GROUP_ID) values (?, ?)', (user.id, group.id)) for group in user.groups]
    db_template.update('delete from T_USER_ROLE where USER_ID = ?', (user.id,))
    if user.roles:
        [db_template.insert('insert into T_USER_ROLE (USER_ID, ROLE_ID) values (?, ?)', (user.id, role.id)) for role in user.roles]

def __db_delete(user):
    db_template.update('delete from T_USER_ROLE where USER_ID = ?', (user.id,))
    db_template.update('delete from T_USER_GROUP where USER_ID = ?', (user.id,))
    db_template.update('delete from T_USER where ID = ?', (user.id,))

def __db_get_root_group():
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where PARENT_ID is null', (), __map_group)
    
def __db_save_group(group):
    group.id = db_template.insert('insert into T_GROUP (NAME, PARENT_ID, DESCRIPTION) values (?, ?, ?)', (group.name, group.parent.id if group.parent else None, group.description))

def __db_get_group(id):
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where ID = ?', (id,), __map_group)
    
def __db_list_group():
    return db_template.query_list('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP', (), __map_group)

def __db_get_group_by_name(name):
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where NAME = ?', (name,), __map_group)

def __db_count_group(keyword):
    sql = 'select count(*) from T_GROUP where 1 = 1'
    params = []
    if keyword:
        sql += ' and (NAME like ? or DESCRIPTION like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    return db_template.query_object(sql, params)

def __db_find_group(keyword, start, count):
    sql = 'select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where 1 = 1'
    params = []
    if keyword:
        sql += ' and (NAME like ? or DESCRIPTION like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    sql += ' order by ID desc limit ?, ?'
    params.extend((start, count))
    return db_template.query_list(sql, params, __map_group)
    
def __db_update_group(group):
    db_template.update('update T_GROUP set NAME = ?, PARENT_ID = ?, DESCRIPTION = ? where ID = ?', (group.name, group.parent.id if group.parent else None, group.description, group.id))
    db_template.update('delete from T_GROUP_ROLE where GROUP_ID = ?', (group.id,))
    if group.roles:
        [db_template.insert('insert into T_GROUP_ROLE (GROUP_ID, ROLE_ID) values (?, ?)', (group.id, role.id)) for role in group.roles]
        
def __db_delete_group(group):
    db_template.update('delete from T_GROUP_ROLE where GROUP_ID = ?', (group.id,))
    db_template.update('delete from T_GROUP where ID = ?', (group.id,))
    
def __db_group_has_child(id):
    return db_template.query_object('select count(*) from T_GROUP where PARENT_ID = ?', (id,)) > 0

def __db_group_be_using(id):
    return db_template.query_object('select count(*) from T_USER_GROUP where GROUP_ID = ?', (id,)) > 0

def __db_find_group_by_user(user_id):
    return db_template.query_list('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where ID in (select GROUP_ID from T_USER_GROUP where USER_ID = ?)', (user_id,), __map_group)

def __db_get_role(id):
    return db_template.query_object('select ID, NAME, DESCRIPTION from T_ROLE where ID = ?', (id,), __map_role)

def __db_list_role():
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE', (), __map_role)
    
def __db_find_role_by_user(user_id):
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE where ID in (select ROLE_ID from T_USER_ROLE where USER_ID = ?)', (user_id,), __map_role)

def __db_find_role_by_group(group_id):
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE where ID in (select ROLE_ID from T_GROUP_ROLE where GROUP_ID = ?)', (group_id,), __map_role)

