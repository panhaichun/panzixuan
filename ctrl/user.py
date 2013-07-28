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
    return mapping.get(re.sub('^/user/\d+', '/user/${id}', path) + '#' + method)

@authorization.protected(name='创建用户', allow_roles=('MANAGEMENT',))
def add(request, response):
    data = {'subtitle': '创建用户', 'parent_id': request.get_param('parent_id')}
    webutil.render('/user/add.html', data, request, response)

@authorization.protected(name='创建用户', allow_roles=('MANAGEMENT',))
def post(request, response):
    pzx.user.create(request.get_param('username'), request.get_param('password'), request.get_param('name'))
    response.redirect('user')

@authorization.protected(name='用户列表', allow_roles=('MANAGEMENT',))
def list(request, response):
    data = {'subtitle': '用户列表'}
    page = request.get_param('page')
    size = request.get_param('size')
    keyword = request.get_param('keyword')
    data['keyword'] = keyword
    data['pagination'] = pzx.user.find(keyword, int(page) if page else 1, int(size) if size else Pagination.DEFAULT_PAGE_SIZE)
    webutil.render('/user/list.html', data, request, response)

@authorization.protected(name='查看用户', allow_roles=('MANAGEMENT',))
def get(request, response):
    data = {'subtitle': '查看用户'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get(int(id))
    webutil.render('/user/view.html', data, request, response)
    
@authorization.protected(name='修改用户', allow_roles=('MANAGEMENT',))
def edit(request, response):
    data = {'subtitle': '修改用户'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get(int(id))
    webutil.render('/user/edit.html', data, request, response)
    
@authorization.protected(name='修改用户', allow_roles=('MANAGEMENT',))
def put(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.user.update(int(id), request.get_param('name'))
    response.redirect('../user')
    
@authorization.protected(name='删除用户', allow_roles=('MANAGEMENT',))
def delete(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.user.delete(int(id))
    response.redirect('../user')

@authorization.protected(name='设置用户密码', allow_roles=('MANAGEMENT',))
def edit_password(request, response):
    data = {'subtitle': '设置用户密码'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get(int(id))
    webutil.render('/user/password_edit.html', data, request, response)
    
@authorization.protected(name='设置用户密码', allow_roles=('MANAGEMENT',))
def put_password(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    pzx.user.update_password(int(id), request.get_param('password'))
    response.redirect('../../user')

@authorization.protected(name='设置用户组', allow_roles=('MANAGEMENT',))
def edit_groups(request, response):
    data = {'subtitle': '设置用户组'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get(int(id))
    data['groups'] = pzx.user.list_group()
    webutil.render('/user/groups_edit.html', data, request, response)
    
@authorization.protected(name='设置用户组', allow_roles=('MANAGEMENT',))
def put_groups(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    group_ids = request.get_params('group_id')
    pzx.user.set_groups(int(id), [int(group_id) for group_id in group_ids] if group_ids else [])
    response.redirect('../../user')

@authorization.protected(name='设置用户角色', allow_roles=('MANAGEMENT',))
def edit_roles(request, response):
    data = {'subtitle': '设置用户角色'}
    id = re.search('\d+', request.get_path()).group(0)
    data['model'] = pzx.user.get(int(id))
    data['roles'] = pzx.user.list_role()
    webutil.render('/user/roles_edit.html', data, request, response)
    
@authorization.protected(name='设置用户角色', allow_roles=('MANAGEMENT',))
def put_roles(request, response):
    id = re.search('\d+', request.get_path()).group(0)
    role_ids = request.get_params('role_id')
    pzx.user.set_roles(int(id), [int(role_id) for role_id in role_ids] if role_ids else [])
    response.redirect('../../user')
    
mapping = {}
mapping['/user/add#get'] = add
mapping['/user#post'] = post
mapping['/user#get'] = list
mapping['/user/${id}#get'] = get
mapping['/user/${id}/edit#get'] = edit
mapping['/user/${id}#put'] = put
mapping['/user/${id}#delete'] = delete
mapping['/user/${id}/password/edit#get'] = edit_password
mapping['/user/${id}/password#put'] = put_password
mapping['/user/${id}/groups/edit#get'] = edit_groups
mapping['/user/${id}/groups#put'] = put_groups
mapping['/user/${id}/roles/edit#get'] = edit_roles
mapping['/user/${id}/roles#put'] = put_roles