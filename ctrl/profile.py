import webutil
import security.authorization as authorization
import pzx.user
import security.authholder as authholder

def dispatch(request):
    path = request.get_path()
    method = request.get_method().lower()
    _method = request.get_param('_method')
    if _method:
        method = _method.lower()
    return mapping.get(path + '#' + method)

@authorization.protected(name='查看自己信息', allow_roles=('USER',))
def get(request, response):
    data = {'subtitle': '我的个人信息'}
    data['model'] = pzx.user.get_self(authholder.principal().get_prototype().id)
    webutil.render('/profile/view.html', data, request, response)

@authorization.protected(name='修改自己信息', allow_roles=('USER',))
def edit(request, response):
    data = {'subtitle': '修改个人信息'}
    data['model'] = pzx.user.get(authholder.principal().get_prototype().id)
    webutil.render('/profile/edit.html', data, request, response)

@authorization.protected(name='修改自己信息', allow_roles=('USER',))
def put(request, response):
    pzx.user.update_self(authholder.principal().get_prototype().id, request.get_param('name'))
    response.redirect('profile')

@authorization.protected(name='修改自己密码', allow_roles=('USER',))
def edit_password(request, response):
    data = {'subtitle': '修改密码'}
    data['model'] = pzx.user.get_self(authholder.principal().get_prototype().id)
    webutil.render('/profile/password_edit.html', data, request, response)

@authorization.protected(name='修改自己密码', allow_roles=('USER',))
def put_password(request, response):
    pzx.user.update_self_password(authholder.principal().get_prototype().id, request.get_param('password'), request.get_param('original_password'))
    response.redirect('../profile')

mapping = {}
mapping['/profile#get'] = get
mapping['/profile/edit#get'] = edit
mapping['/profile#put'] = put
mapping['/profile/password/edit#get'] = edit_password
mapping['/profile/password#put'] = put_password