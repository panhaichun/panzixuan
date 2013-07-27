import hashlib
import config

class MD5Encryptor:

    def __init__(self, encoding='UTF-8'):
        self.encoding = encoding
        
    def encrypt(self, src):
        if src:
            src = src.strip()
        if not src:
            return src
        md = hashlib.md5()
        md.update(src.encode(self.encoding))
        return md.hexdigest()

DEFAULT_ENCRYPTOR = MD5Encryptor(config.encoding)
