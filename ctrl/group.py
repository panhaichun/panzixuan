import re
import webutil
import security.authorization as authorization
import pzx.user
from pzx.pagination import Pagination

def dispatch(request):
    path = request.get_path()
    method = request.get_method().lower()
    _method = request.get_param('_method')
    if _method:
        method = _method.lower()
    return mapping.get(re.sub('^/group/\d+', '/group/${id}', path) + '#' + method)

@authorization.protected(name='创建组', allow_roles=('MANAGEMENT',))
def add(request, response):
    data = {'subtitle': '创建组', 'parent_id': request.get_param('parent_id')}
    webutil.render('/group/add.html', data, request, response)

@authorization.protected(name='创建组', allow_roles=('MANAGEMENT',))
def post(request, response):
    parent_id = request.get_param('parent_id')
    pzx.user.create_group(request.get_param('name'), request.get_param('description'), int(parent_id) if parent_id else None)
    response.redirect('group')

@authorization.protected(name='组列表', allow_roles=('MANAGEMENT',))
def list(request, response):
    data = {'subtitle': '组列表'}
    page = request.get_param('page')
    size = request.get_param('size')
    keyword = request.get_param('keyword')
    data['keyword'] = keyword
    data['pagination'] = pzx.user.find_group(keyword, int(page) if page else 1, int(size) if size else Pagination.DEFAULT_PAGE_SIZE)
    webutil.render('/group/list.html', data, request, response)

@authorization.protected(name='查看组', allow_roles=('MANAGEMENT',))
def get(request, response):
    data = {'subtitle': '查看组'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get_group(int(id))
    webutil.render('/group/view.html', data, request, response)
    
@authorization.protected(name='修改组', allow_roles=('MANAGEMENT',))
def edit(request, response):
    data = {'subtitle': '修改组'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get_group(int(id))
    webutil.render('/group/edit.html', data, request, response)
    
@authorization.protected(name='修改组', allow_roles=('MANAGEMENT',))
def put(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.user.update_group(int(id), request.get_param('name'), request.get_param('description'))
    response.redirect('../group')
    
@authorization.protected(name='删除组', allow_roles=('MANAGEMENT',))
def delete(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.user.delete_group(int(id))
    response.redirect('../group')

@authorization.protected(name='设置组角色', allow_roles=('MANAGEMENT',))
def edit_roles(request, response):
    data = {'subtitle': '设置组角色'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get_group(int(id))
    data['roles'] = pzx.user.list_role()
    webutil.render('/group/roles_edit.html', data, request, response)
    
@authorization.protected(name='设置组角色', allow_roles=('MANAGEMENT',))
def put_roles(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    role_ids = request.get_params('role_id')
    pzx.user.set_group_roles(int(id), [int(role_id) for role_id in role_ids] if role_ids else [])
    response.redirect('../../group')
    
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