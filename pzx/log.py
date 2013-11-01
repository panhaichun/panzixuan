import time

from pzx.db import db_template
from pzx.pagination import Pagination
from pzx.user import User

class Log:

    def __init__(self, id=None, time=None, operator=None, resource_name=None, resource_path=None, arguments=None, status=None, message=None):
        self.id = id
        self.time = time
        self.operator = operator
        self.resource_name = resource_name
        self.resource_path = resource_path
        self.arguments = arguments
        self.status = status
        self.message = message
    
    def __eq__(self, obj):
        if self is obj:
            return True
        return self.id == obj.id if isinstance(obj, Log) else False

    def __hash__(self):
        return hash(self.id) if self.id else hash(self)
        
    def __str__(self):
        return 'Log [time=%s, operator=%d, resource_path=%s]' % (str(self.time), self.operator.name, self.resource_path)
        
class LogNotFoundException(Exception):
    pass

def create():

def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    log = __repo_get(id)
    if not log:
        raise LogNotFoundException('日志ID[%d]不存在' % id)
    return log

def find(conditions, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    total = __repo_count(conditions)
    start = (number - 1) * size
    return Pagination(number, size, total, __repo_find(conditions, start, size)) if total > start else Pagination(number, size, 0, [])
    
def find_by_user(user_id, conditions, number, size):
    if number < 1:
        raise ValueError('参数[number]不能小于1')
    if size < 1:
        raise ValueError('参数[size]不能小于1')
    __conditions = conditions.copy().update({'operator': user_id})
    total = __repo_count(__conditions)
    start = (number - 1) * size
    return Pagination(number, size, total, __repo_find(__conditions, start, size)) if total > start else Pagination(number, size, 0, [])
    
def delete(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    __repo_delete(get(id))

def clean_before(time):
    if not time:
        raise ValueError('参数[time]不能为空')
    __repo_delete_before(time)

def __map(data):
    operator = User(id=data[2], username=data[3], name=data[4])
    return Log(data[0], data[1], operator, data[5], data[6], data[7], data[8], data[9])
    
def __repo_save(log):
    log.id = db_template.insert('insert into T_LOG (TIME, OPERATOR, RESOURCE_NAME, RESOURCE_PATH, ARGUMENTS, STATUS, MESSAGE) VALUES (?, ?, ?, ?, ?, ?, ?)', (log.time, log.operator, log.resource_name, log.resource_path, log.arguments, log.status, log.message))

def __repo_get(id):
    return db_template.query_object('select L.ID, L.TIME, L.OPERATOR, U.USERNAME, U.NAME, L.RESOURCE_NAME, L.RESOURCE_PATH, L.ARGUMENTS, L.STATUS, L.MESSAGE from T_LOG L inner join T_USER U on L.OPERATOR = U.ID where L.ID = ?', (id,), __map)

def __repo_count(conditions):
    sql = 'select count(*) from T_LOG L inner join T_USER U on L.OPERATOR = U.ID where 1 = 1'
    params = []
    if conditions:
        operator = conditions.get('operator')
        if operator:
            sql += ' and L.OPERATOR = ?'
            params.append(operator)
        operator_name = conditions.get('operator_name')
        if operator_name:
            sql += ' and (U.USERNAME like ? or U.NAME like ?)'
            param = '%' + operator_name + '%'
            params.extend((operator_name, operator_name))
        start_time = conditions.get('start_time')
        if start_time:
            sql += " and L.TIME >= ?";
            params.append(start_time)
        end_time = conditions.get('end_time')
        if end_time:
            sql += " and L.TIME <= ?";
            params.append(end_time)
        resource_name = conditions.get('resource_name')
        if resource_name:
            sql += ' and L.RESOURCE_NAME like ?'
            param = '%' + resource_name + '%'
            params.append(resource_name)
        status = conditions.get('status')
        if status:
            sql += ' and L.STATUS = ?'
            params.append(status)
    return db_template.query_object(sql, params)

def __repo_find(conditions, start, count):
    sql = 'select L.ID, L.TIME, L.OPERATOR, U.USERNAME, U.NAME, L.RESOURCE_NAME, L.RESOURCE_PATH, L.ARGUMENTS, L.STATUS, L.MESSAGE from T_LOG L inner join T_USER U on L.OPERATOR = U.ID where 1 = 1'
    params = []
    if conditions:
       operator = conditions.get('operator')
        if operator:
            sql += ' and L.OPERATOR = ?'
            params.append(operator)
        operator_name = conditions.get('operator_name')
        if operator_name:
            sql += ' and (U.USERNAME like ? or U.NAME like ?)'
            param = '%' + operator_name + '%'
            params.extend((operator_name, operator_name))
        start_time = conditions.get('start_time')
        if start_time:
            sql += " and L.TIME >= ?";
            params.append(start_time)
        end_time = conditions.get('end_time')
        if end_time:
            sql += " and L.TIME <= ?";
            params.append(end_time)
        resource_name = conditions.get('resource_name')
        if resource_name:
            sql += ' and L.RESOURCE_NAME like ?'
            param = '%' + resource_name + '%'
            params.append(resource_name)
        status = conditions.get('status')
        if status:
            sql += ' and L.STATUS = ?'
            params.append(status)
    sql += ' order by L.ID desc limit ?, ?'
    params.extend((start, count))
    return db_template.query_list(sql, params, __map)

def __repo_delete(log):
    db_template.update('delete from T_LOG where ID = ?', (log.id,))

def __repo_delete_befor(time):
    db_template.update("delete from T_LOG where TIME <= ?", (time,))