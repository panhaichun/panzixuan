# -*- coding: UTF-8 -*-

from datetime import datetime
from website.base.db import db_template
from website.base.entity import Entity

import mimetypes
import os
import website.base.context as context

class Attachment(Entity):
    
    DEFAULT_NAME = "unnamed"
    
    def __init__(self, _id=None, name=None, content_type=None, size=None, path=None, owner=None, upload_time=datetime.now()):
        Entity.__init__(self, _id)
        if not name or name.isspace():
            self.name = Attachment.DEFAULT_NAME
        else:
            self.name = name.strip()
        self.content_type = content_type
        self.size = size
        self.path = path
        self.owner = owner
        self.upload_time = upload_time


FS_DIR = "/fs"

def get(_id):
    return __db_get(_id)

def open_attachment(attachment):
    if attachment is None:
        raise ValueError, "参数 [attachment] 不能为空"
    return open(context.install_path + FS_DIR + "/" + attachment.path, "rb")

def delete(id_array):
    if not id_array:
        raise ValueError, "参数 [id_array] 不能为空"
    for _id in id_array:
        attachment = get(_id)
        __db_delete(_id)
        os.remove(context.install_path + FS_DIR + "/" + attachment.path)

def upload(name, content_type, _file, _user):
    if _file is None:
        raise ValueError, "参数 [_file] 不能为空"
    filename = _file.name
    suffix = ""
    if filename:
        index = filename.strip().rfind(".")
        if index > 0:
            suffix = filename[index:]
    upload_time = datetime.now()
    filename = "%d%s" % (int(datetime.strftime(upload_time, "%Y%m%d%H%M%S%f")) + abs(hash(name)) * 19 + abs(hash(filename)) * 23, suffix)
    filepath = context.install_path + FS_DIR + "/" + filename
    upload_file = open(filepath, "wb")
    
    size = 0
    for line in _file:
        size += len(line)
        upload_file.write(line)
    upload_file.close()
    owner = _user.id if _user else None
    content_type = content_type.strip() if content_type else mimetypes.guess_type(filepath)[0]
    attachment = Attachment(None, name, content_type, size, filename, owner, upload_time)
    __db_save(attachment);
    return attachment


def __map_attachment(data):
    if not data:
        return None
    return Attachment(data[0], data[1], data[2], data[3], data[4], data[5], data[6])

def __db_save(attachment):
    params = (attachment.name, attachment.content_type, attachment.size, attachment.path, attachment.owner, attachment.upload_time)
    _id = db_template.insert("INSERT INTO WBST_ATTACHMENT (NAME, CONTENT_TYPE, SIZE, PATH, OWNER_ID, UPLOAD_TIME) VALUES (%s, %s, %s, %s, %s, %s)", params)
    attachment.id = _id

def __db_get(_id):
    return db_template.query_object("SELECT ID, NAME, CONTENT_TYPE, SIZE, PATH, OWNER_ID, UPLOAD_TIME FROM WBST_ATTACHMENT WHERE ID = %s", (_id), __map_attachment)

def __db_delete(_id):
    db_template.update("DELETE FROM WBST_ATTACHMENT WHERE ID = %s", (_id))
