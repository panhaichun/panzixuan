from pzx.db import db_template

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
        return 'Role [name=%s]' % self.name
        
class RoleNotFoundException(Exception):
    pass

def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    role = __repo_get(id)
    if not role:
        raise RoleNotFoundException('角色ID[%s]不存在' % id)
    return role

def list():
    return __repo_list()

def list_by_group(group_id):
    return __repo_find_by_group(group_id)

def list_by_user(user_id):
    return __repo_find_by_user(user_id)
    
def __map(data):
    return Role(data[0], data[1], data[2])
    
def __repo_get(id):
    return db_template.query_object('select ID, NAME, DESCRIPTION from T_ROLE where ID = ?', (id,), __map)

def __repo_list():
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE where IS_GROUP = 0', (), __map)

def __repo_find_by_group(group_id):
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE where ID in (select ROLE_ID from T_GROUP_ROLE where GROUP_ID = ?)', (group_id,), __map)

def __repo_find_by_user(user_id):
    return db_template.query_list('select ID, NAME, DESCRIPTION from T_ROLE where ID in (select ROLE_ID from T_USER_ROLE where USER_ID = ?)', (user_id,), __map)
