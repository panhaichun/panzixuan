from datetime import datetime
from pzx.db import db_template
from pzx.pagination import Pagination

import mimetypes
import os
import config

FS_DIR = '/file'

class Attachment:
    
    DEFAULT_NAME = '未命名'
    
    def __init__(self, id=None, name=None, content_type=None, size=None, path=None, owner=None, upload_time=datetime.now()):
        self.id = id
        self.name = name if name or name.isspace() else Attachment.DEFAULT_NAME
        self.content_type = content_type
        self.size = size
        self.path = path
        self.owner = owner
        self.upload_time = upload_time
        
    def open(self):
        return open(config.install_path + FS_DIR + self.path, 'rb')
        
class AttachmentNotFoundException(Exception):
    pass
class FileNotFoundException(Exception):
    pass

def upload(name, content_type, file, user):
    if file is None:
        raise ValueError, '参数 [file] 不能为空'
    filename = file.name
    suffix = ''
    if filename:
        index = filename.strip().rfind('.')
        if index > 0:
            suffix = filename[index:]
    upload_time = datetime.now()
    filename = '%d%s' % (int(datetime.strftime(upload_time, '%Y%m%d%H%M%S%f')) + abs(hash(name)) * 19 + abs(hash(filename)) * 23, suffix)
    filepath = context.install_path + FS_DIR + '/' + filename
    upload_file = open(filepath, 'wb')
    
    size = 0
    for line in file:
        size += len(line)
        upload_file.write(line)
    upload_file.close()
    owner = user.id if user else None
    content_type = content_type.strip() if content_type else mimetypes.guess_type(filepath)[0]
    attachment = Attachment(None, name, content_type, size, '/' + filename, owner, upload_time)
    __db_save(attachment);
    return attachment

def get(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    attachment = __db_get(id)
    if not attachment:
        raise AttachmentNotFoundException('附件id[%d]不存在' % id)

def delete(id):
    if not id:
        raise ValueError('参数[id]不能为空')
    attachment = get(id)
    __db_delete(id)
    os.remove(config.install_path + FS_DIR + attachment.path)

def __map_attachment(data):
    if not data:
        return None
    return Attachment(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

def __db_save(attachment):
    params = (attachment.name, attachment.content_type, attachment.size, attachment.path, attachment.owner, attachment.upload_time)
    attachment.id = db_template.insert('insert into T_ATTACHMENT (NAME, CONTENT_TYPE, SIZE, PATH, OWNER_ID, UPLOAD_TIME) values (?, ?, ?, ?, ?, ?)', params)

def __db_get(id):
    return db_template.query_object('select ID, NAME, CONTENT_TYPE, SIZE, PATH, OWNER_ID, UPLOAD_TIME from T_ATTACHMENT WHERE ID = ?', (id,), __map_attachment)

def __db_delete(id):
    db_template.update('delete from T_ATTACHMENT WHERE ID = ?', (id,))
