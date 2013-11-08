import re
import webutil
import security.authorization as authorization
import pzx.group, pzx.role
from pzx.pagination import Pagination

def dispatch(request):
    path = request.get_path()
    method = request.get_method().lower()
    _method = request.get_param('_method')
    if _method:
        method = _method.lower()
    return mapping.get(re.sub('^/group/\d+', '/group/${id}', path) + '#' + method)

@authorization.protected(name='创建组', allow_roles=('SYS_USER',))
def add(request, response):
    data = {'title': '系统管理 - 组 - 创建', 'parent_id': request.get_param('parent_id')}
    webutil.render('/group/add.html', data, request, response)

@authorization.protected(name='创建组', allow_roles=('SYS_USER',))
def post(request, response):
    parent_id = request.get_param('parent_id')
    group = pzx.group.create(request.get_param('name'), request.get_param('description'), int(parent_id) if parent_id else None)
    response.redirect('group/' + str(group.id))

@authorization.protected(name='组列表', allow_roles=('SYS_USER',))
def list(request, response):
    data = {'title': '系统管理 - 组 - 列表'}
    page = request.get_param('page')
    size = request.get_param('size')
    keyword = request.get_param('keyword')
    data['keyword'] = keyword
    data['pagination'] = pzx.group.find(keyword, int(page) if page else 1, int(size) if size else Pagination.DEFAULT_PAGE_SIZE)
    webutil.render('/group/list.html', data, request, response)

@authorization.protected(name='查看组', allow_roles=('SYS_USER',))
def get(request, response):
    data = {'title': '系统管理 - 组 - 查看'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.group.get(int(id))
    webutil.render('/group/view.html', data, request, response)
    
@authorization.protected(name='修改组', allow_roles=('SYS_USER',))
def edit(request, response):
    data = {'title': '系统管理 - 组 - 修改'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.group.get(int(id))
    webutil.render('/group/edit.html', data, request, response)
    
@authorization.protected(name='修改组', allow_roles=('SYS_USER',))
def put(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.group.update(int(id), request.get_param('name'), request.get_param('description'))
    response.redirect('../group/' + id)
    
@authorization.protected(name='删除组', allow_roles=('SYS_USER',))
def delete(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.group.delete(int(id))
    response.redirect('../group')

@authorization.protected(name='设置组角色', allow_roles=('SYS_USER',))
def edit_roles(request, response):
    data = {'title': '系统管理 - 组 - 设置角色'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.group.get(int(id))
    data['roles'] = pzx.role.list()
    webutil.render('/group/roles_edit.html', data, request, response)
    
@authorization.protected(name='设置组角色', allow_roles=('SYS_USER',))
def put_roles(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    role_ids = request.get_params('role_id')
    pzx.group.set_roles(int(id), [int(role_id) for role_id in role_ids] if role_ids else [])
    response.redirect('../../group/' + id)
    
mapping = {}
mapping['/group/add#get'] = add
mapping['/group#post'] = post
mapping['/group#get'] = list
mapping['/group/${id}#get'] = get
mapping['/group/${id}/edit#get'] = edit
mapping['/group/${id}#put'] = put
mapping['/group/${id}#delete'] = delete
mapping['/group/${id}/roles/edit#get'] = edit_roles
mapping['/group/${id}/roles#put'] = put_roles