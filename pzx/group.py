import time

from pzx.db import db_template
from pzx.pagination import Pagination
import pzx.role

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
        return 'Group [name=%s]' % self.name
      
class GroupNotFoundException(Exception):
    pass
class IncompleteGroupException(Exception):
    pass
class DuplicateGroupNameException(Exception):
    pass
class GroupBeUsingException(Exception):
    pass

def create(name, description, parent_id):
    if not name or len(name) > 32:
        raise IncompleteGroupException('名称不能为空，且长度不能超过32个字符')
    if description and len(description) > 128:
        raise IncompleteGroupException('描述长度不能超过128个字符')
    parent = None
    if parent_id is None:
        parent = __repo_get_root()
    else:
        try:
            parent = get(parent_id)
        except GroupNotFoundException:
            raise IncompleteGroupException('父组ID[%d]不存在' % parent_id)
    if __repo_get_by_name(name):
        raise DuplicateGroupNameException('组名称[%s]已存在' % name)
    group = Group(None, name, parent, description)
    __repo_save(group)
    return group
    
def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    group = __repo_get(id)
    if not group:
        raise GroupNotFoundException('组ID[%s]不存在' % id)
    return group

def list():
    return __repo_list()
    
def list_by_user(user_id):
    return __repo_find_by_user(user_id)

def find(keyword, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    total = __repo_count(keyword)
    start = (number - 1) * size
    return Pagination(number, size, total, __repo_find(keyword, start, size)) if total > start else Pagination(number, size, 0, [])
    
def update(id, name, description):
    group = get(id)
    if not name or len(name) > 32:
        raise IncompleteGroupException('名称不能为空，且长度不能超过32个字符')
    if description and len(description) > 128:
        raise IncompleteGroupException('描述长度不能超过128个字符')
    another = __repo_get_by_name(name)
    if another and not id == another.id:
        raise DuplicateGroupNameException('组名 [%s] 已存在' % name)
    if not name == group.name and group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]名称不允许修改' % group.name)
    group.name = name
    group.description = description
    __repo_update(group)
    return group
    
def delete(id):
    group = get(id)
    if group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]不允许删除' % group.name)
    if __repo_has_child(id):
        raise GroupBeUsingException('组[%d]包含子组, 不能删除' % id)
    if __repo_be_using(id):
        raise GroupBeUsingException('组[%d]正在被用户使用, 不能删除' % id)
    __repo_delete(group)

def set_roles(id, role_ids):
    group = get(id)
    if group.name in (group.ADMIN_GROUP_NAME, group.ROOT_GROUP_NAME):
        raise IncompleteGroupException('组[%s]角色不允许修改' % group.name)
    group.roles = set()
    if role_ids:
        group.roles.update([pzx.role.get(role_id) for role_id in role_ids])
    __repo_update(group)

def __map(data):
    group = Group(data[0], data[1], __repo_get(data[2]) if data[2] else None, data[3])
    group.roles.update(pzx.role.list_by_group(group.id))
    return group

def __repo_get_root():
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where PARENT_ID is null', (), __map)
    
def __repo_save(group):
    group.id = db_template.insert('insert into T_GROUP (NAME, PARENT_ID, DESCRIPTION) values (?, ?, ?)', (group.name, group.parent.id if group.parent else None, group.description))

def __repo_get(id):
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where ID = ?', (id,), __map)

def __repo_get_by_name(name):
    return db_template.query_object('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where NAME = ?', (name,), __map)
    
def __repo_list():
    return db_template.query_list('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP', (), __map)

def __repo_find_by_user(user_id):
    return db_template.query_list('select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where ID in (select GROUP_ID from T_USER_GROUP where USER_ID = ?)', (user_id,), __map)

def __repo_count(keyword):
    sql = 'select count(*) from T_GROUP where 1 = 1'
    params = []
    if keyword:
        sql += ' and (NAME like ? or DESCRIPTION like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    return db_template.query_object(sql, params)

def __repo_find(keyword, start, count):
    sql = 'select ID, NAME, PARENT_ID, DESCRIPTION from T_GROUP where 1 = 1'
    params = []
    if keyword:
        sql += ' and (NAME like ? or DESCRIPTION like ?)'
        param = '%' + keyword + '%'
        params.extend((param, param))
    sql += ' order by ID desc limit ?, ?'
    params.extend((start, count))
    return db_template.query_list(sql, params, __map)
    
def __repo_update(group):
    db_template.update('update T_GROUP set NAME = ?, PARENT_ID = ?, DESCRIPTION = ? where ID = ?', (group.name, group.parent.id if group.parent else None, group.description, group.id))
    db_template.update('delete from T_GROUP_ROLE where GROUP_ID = ?', (group.id,))
    if group.roles:
        [db_template.insert('insert into T_GROUP_ROLE (GROUP_ID, ROLE_ID) values (?, ?)', (group.id, role.id)) for role in group.roles]
        
def __repo_delete(group):
    db_template.update('delete from T_GROUP_ROLE where GROUP_ID = ?', (group.id,))
    db_template.update('delete from T_GROUP where ID = ?', (group.id,))
    
def __repo_has_child(id):
    return db_template.query_object('select count(*) from T_GROUP where PARENT_ID = ?', (id,)) > 0

def __repo_be_using(id):
    return db_template.query_object('select count(*) from T_USER_GROUP where GROUP_ID = ?', (id,)) > 0
