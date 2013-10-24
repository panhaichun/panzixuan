import logging
import io
import re
import urllib
from server.wsgiserver import HTTPServer
import dispatcher
import config

class Request:
    '''
    Request
    '''
    def __init__(self, environs, encoding):
        self.__headers = {}
        [self.__headers.update({re.sub('^HTTP_', '', e).upper(): environs[e]}) for e in environs if e.startswith('HTTP_')]
        self.__environs = environs
        self.__params = None
        self.__input = environs.get('wsgi.input')
        self.__encoding = encoding
        
    def get_header(self, name, default=None):
        return self.__headers.get(name.upper(), default)
        
    def get_headers(self):
        return self.__headers.copy()
        
    def get_protocol(self):
        return self.__environs.get('SERVER_PROTOCOL')
    
    def get_ctx_path(self):
        return config.ctx_path
        
    def get_method(self):
        return self.__environs.get('REQUEST_METHOD')
        
    def get_content_type(self):
        return self.__environs.get('CONTENT_TYPE', '')
        
    def get_content_length(self):
        len = self.__environs.get('CONTENT_LENGTH')
        return int(len) if len else 0
        
    def get_path(self):
        return self.__environs.get('PATH_INFO')
        
    def get_query_string(self):
        return self.__environs.get('QUERY_STRING')
        
    def get_remote_addr(self):
        return self.__environs.get('REMOTE_ADDR')
        
    def get_server_port(self):
        return port
        
    def get_param(self, name, default=None):
        values = self.get_params(name)
        return values[0] if values is not None else default
        
    def get_params(self, name, default=None):
        if self.__params is None:
            self.__build_params()
        return self.__params[name] if name in self.__params else default
    
    def get_all_params(self):
        if self.__params is None:
            self.__build_params()
        return self.__params.copy()
    
    def get_cookies(self):
        cookies = {}
        cookie = self.get_header('COOKIE')
        kvs = cookie.strip().split(';') if cookie else ''
        for kv in kvs:
            if '=' in kv:
                name, value = kv.strip().split('=', 1)
                name = name.strip()
                if name:
                    cookies[name] = urllib.parse.unquote(value.strip(), self.__encoding)
        return cookies
    
    def set_encoding(slef, encoding):
        self.__encoding = encoding
    
    def get_encoding(self):
        return self.__encoding
        
    def __build_params(self):
        self.__params = {}
        self.__parse_params(self.get_query_string().strip())
        if self.get_content_length() > 0:
            if not self.get_content_type().startswith('multipart/form-data'):
                self.__parse_params(self.__input.getvalue().decode(self.__encoding).strip())
            else:
                # 比较难搞，以后实现
                pass
                
    def __parse_params(self, str):
        if not str:
            return
        [self.__put_params(kv.strip().split('=', 1)) for kv in str.split('&') if '=' in kv]
                
    def __put_params(self, kv):
        name = kv[0].strip()
        if not name:
            return
        value = urllib.parse.unquote(kv[1].strip())
        if name in self.__params:
            self.__params[name].append(value)
        else:
            self.__params[name] = [value]

class Response:
    '''
    Response
    '''
    RESPONSES = {
        100: 'Continue',
        101: 'Switching Protocols',
        
        200: 'OK',
        201: 'Created',
        202: 'Accepted',
        203: 'Non-Authoritative Information',
        204: 'No Content',
        205: 'Reset Content',
        206: 'Partial Content',
        
        300: 'Multiple Choices',
        301: 'Moved Permanently',
        302: 'Found',
        303: 'See Other',
        304: 'Not Modified',
        305: 'Use Proxy',
        307: 'Temporary Redirect',
        
        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Payment Required',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        406: 'Not Acceptable',
        407: 'Proxy Authentication Required',
        408: 'Request Timeout',
        409: 'Conflict',
        410: 'Gone',
        411: 'Length Required',
        412: 'Precondition Failed',
        413: 'Request Entity Too Large',
        414: 'Request-URI Too Long',
        415: 'Unsupported Media Type',
        416: 'Requested Range Not Satisfiable',
        417: 'Expectation Failed',
        428: 'Precondition Required',
        429: 'Too Many Requests',
        431: 'Request Header Fields Too Large',

        500: 'Internal Server Error',
        501: 'Not Implemented',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
        505: 'HTTP Version Not Supported',
        511: 'Network Authentication Required',
    }
    DEFAULT_STATUS = 200
    def __init__(self, out, encoding):
        self.write = lambda obj: out.write(obj) if isinstance(obj, bytes) or isinstance(obj, bytearray) else out.write(str(obj).encode(encoding))
        self.__reset = lambda: out.truncate(0)
        self.__status = (self.DEFAULT_STATUS, self.RESPONSES[self.DEFAULT_STATUS])
        self.__headers = {'Content-Type': 'text/html; charset=' + encoding}
        self.__cookies = []
        
    def set_status(self, status, pharse=None):
        if status is None or not 100 <= status <= 599:
            raise ValueError('参数[status]不能为空且必须取值为100-599之间')
        self.__status = (status, (self.RESPONSES[status] if status in self.RESPONSES else '') if pharse is None else pharse)
        
    def get_status(self):
        return self.__status
        
    def set_content_type(self, content_type):
        self.set_header('Content-Type', content_type)
        
    def set_content_length(self, content_length):
        self.set_header('Content-Length', content_length)
        
    def set_header(self, name, value):
        if not name:
            raise ValueError('参数[name]不能为空')
        self.__headers[str(name)] = str(value) if value is not None else ''
    
    def set_cookie(self, name, value, path, domain, expires=None, comment=None, version=None, secure=False):
        if not name:
            raise ValueError('参数[name]不能为空')
        if not path:
            raise ValueError('参数[path]不能为空')
        if not domain:
            raise ValueError('参数[domain]不能为空')
        self.__cookies.append((name, value, path, domain, expires, comment, version, secure))
        
    def redirect(self, location):
        self.set_status(302)
        self.set_header('Location', location)
        
    def reset(self):
        '''
        清除写缓冲，重置Status、Http Headers、Cookies
        '''
        self.__reset()
        self.__status = (self.DEFAULT_STATUS, self.RESPONSES[self.DEFAULT_STATUS])
        self.__headers = {}
        self.__cookies = []
        
    def get_headers(self):
        return self.__headers.copy()
        
    def get_cookies(self):
        return self.__cookies[:]

def application(env, start_response):
    request = Request(env, config.encoding)
    out = io.BytesIO()
    response = Response(out, config.encoding)
    try:
        dispatcher.dispatch(request, response)
    except Exception as e:
        start_response('%d %s' % (500, 'Internal Server Error'), {})
    else:
        headers = response.get_headers()
        cookies = response.get_cookies()
        if cookies:
            cookien = 0
            cookiev = ''
            for cookie in response.get_cookies():
                if cookien > 0:
                    cookiev = cookiev + '\r\nSet-Cookie: '
                cookiev = cookiev + ('%s=%s' % (cookie[0], str(cookie[1])))
                if (cookie[2]):
                    cookiev = cookiev + ('; path=%s' % cookie[2])
                if (cookie[3]):
                    cookiev = cookiev + ('; domain=%s' % cookie[3])
                if (cookie[4]):
                    cookiev = cookiev + ('; expires=%s' % str(cookie[4]))
                if (cookie[5]):
                    cookiev = cookiev + ('; comment=%s' % cookie[5])
                if (cookie[6]):
                    cookiev = cookiev + ('; version=%s' % str(cookie[6]))
                if (cookie[7]):
                    cookiev = cookiev + ('; [secure]')
                cookien = cookien + 1
            headers['Set-Cookie'] = cookiev
        write = start_response('%d %s' % response.get_status(), headers)
        content = out.getvalue()
        if content:
            write(content)

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, 
                format='%(threadName)s %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', 
                datefmt='%Y-%m-%d %H:%M:%S',
                file=config.log_file,
                filemode='w')
    HTTPServer(config.port, application).start()