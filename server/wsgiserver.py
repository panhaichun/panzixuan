import collections
import io
import logging
import socket
import sys, os
import traceback
import urllib.parse
import server.nioserver as server

__all__ = ['HTTPServer']

SERVER_PROTOCOL_VERSION = 'HTTP/1.1'
SERVER_VERSION_NUMBER = (1, 1) # 不支持低版本的http协议

DEFAULT_PORT = 8000
DEFAULT_ENCODING = 'UTF-8'

class HTTPServer:

    def __init__(self, port=DEFAULT_PORT, encoding=DEFAULT_ENCODING, application=None):
        self.set_port(port)
        self.set_encoding(encoding)
        self.set_application(application)
        
    def set_port(self, port):
        if port is None or port < 1:
            raise ValueError('参数[port]不能小于1')
        self.port = port

    def set_encoding(self, encoding):
        if encoding is None:
            raise ValueError('参数[encoding]不能为空')
        self.encoding = encoding
        
    def set_application(self, application):
        if application is None:
            raise ValueError('参数[application]不能为空')
        self.application = application
        
    def start(self):
        env = {}
        env['SERVER_PROTOCOL'] = SERVER_PROTOCOL_VERSION
        env['SERVER_NAME'] = ''     # 暂为空
        env['SERVER_PORT'] = self.port
        s = server.NIOServer(address=('', self.port), 
                        sockopts=((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),), 
                        decode = lambda session, bytes: parse_request(session, bytes, self.encoding), 
                        exec_nr_threads=8, 
                        handler=HttpHandler(self.application, self.encoding, env))
        s.daemonize()
        s.start()

class HttpRequest:
    def __init__(self):
        self.method = None
        self.path = None
        self.version = None
        self.headers = {}
        self.input = None
    
class DecodeCtx:
    def __init__(self):
        self.match_crlf = False
        self.request = None
        self.line = bytearray()
        self.input_remain = 0

CR = 13
LF = 10

def parse_request_line(line):
    '''
    解释请求头第一行
    '''
    words = line.split()
    if len(words) == 3:
        version = words[2]
        if version[:5] != 'HTTP/':
            logging.warn('不能识别协议[%s]' % version)
            raise Exception
        version_number = version.split('/', 1)[1].split(".")
        if len(version_number) != 2:
            logging.warn('不能识别Http协议版本[%s]' % version)
            raise Exception
        version_number = int(version_number[0]), int(version_number[1])
        if not version_number >= SERVER_VERSION_NUMBER:
            logging.warn('不兼容Http协议版本[%s]' % version)
            raise Exception
        request = HttpRequest()
        request.method, request.path, request.version = words
        return request
    else:
        logging.warn('不能识别请求行[%s]' % line)
        raise Exception
        
def parse_request_header(line):
    '''
    解释请求头
    '''
    words = line.split(': ', 1)
    if len(words) == 2:
        return (words[0], words[1])
    else:
        logging.warn('不能识别请求头[%s]' % line)
        raise Exception
    
def parse_request(session, bytes, encoding):
    if not bytes:
        return None
    if not session.attributes.get('decode_ctx'):
        session.attributes['decode_ctx'] = DecodeCtx()
    ctx = session.attributes['decode_ctx']
    
    if ctx.input_remain > 0:
        blen = len(bytes)
        if blen < ctx.input_remain:
            ctx.request.input.write(bytes)
            ctx.input_remain -= blen
            return None
        ctx.request.input.write(bytes[0: ctx.input_remain]) # 应该没有多余的字节，对不遵守Http协议的客户端不予支持
        ctx.input_remain = 0
        del session.attributes['decode_ctx']
        return (ctx.request,)
    
    result = []
    bytes = bytearray(bytes)
    while bytes:
        b = bytes.pop(0)
        if b not in (CR, LF):
            # 普通字节，根据Http协议，在请求头中，不会出现单一CR或LF的情况
            if ctx.match_crlf:
                ctx.match_crlf = False
            ctx.line.append(b)
            continue
        if b == CR:
            continue
        # b == LF的情况
        if not ctx.match_crlf:
            # 匹配一行
            ctx.match_crlf = True
            if not ctx.request:
                try:
                    ctx.request = parse_request_line(str(ctx.line, encoding))
                except Exception:
                    session.write(('%s 400 Bad Request\r\nConnection: close\r\n\r\n' % SERVER_PROTOCOL_VERSION).encode(encoding))
                    del session.attributes['decode_ctx']
                    session.close()
                    return None
            else:
                try:
                    name, value = parse_request_header(str(ctx.line, encoding))
                    ctx.request.headers[name.upper()] = value
                except Exception:
                    session.write(('%s 400 Bad Request\r\nConnection: close\r\n\r\n' % SERVER_PROTOCOL_VERSION).encode(encoding))
                    del session.attributes['decode_ctx']
                    session.close()
                    return None
            ctx.line = bytearray()
        else:
            # 此时说明匹配一个Http请求，包括Header
            ctx.match_crlf = False
            # 支持 Expect: 100-Continue
            if ctx.request.headers.get('EXPECT', '').lower() == '100-Continue'.lower():
                session.write(('%s 100 Continue\r\n\r\n' % SERVER_PROTOCOL_VERSION).encode(encoding))
            # 解释Http头，如果有Content-Length，则继续接收数据，否则
            ctlen = int(ctx.request.headers.get('CONTENT-LENGTH', '0'))
            if ctlen:
                ctx.input_remain = ctlen # 还需接收 Content-Length 个字节
                ctx.request.input = io.BytesIO()
                blen = len(bytes)
                if blen < ctx.input_remain:
                    ctx.request.input.write(bytes)
                    ctx.input_remain -= blen
                    return None
                ctx.request.input.write(bytes[0: ctx.input_remain])
                ctx.input_remain = 0
            del session.attributes['decode_ctx']
            return (ctx.request,)
    return None
        
class HttpHandler:

    def __init__(self, application, encoding, environ):
        self.application = application
        self.encoding = encoding
        self.base_env = environ
    
    def __process_data(self, session, data):
        env = self.base_env.copy()
        env['REQUEST_METHOD'] = data.method
        env['SCRIPT_NAME'] = ''
        env['PATH_INFO'] = urllib.parse.unquote(data.path.split('?', 1)[0]) if '?' in data.path else urllib.parse.unquote(data.path)
        env['QUERY_STRING'] = data.path.split('?', 1)[1] if '?' in data.path else ''
        env['CONTENT_TYPE'] = data.headers.get('CONTENT-TYPE', '')
        content_len = data.headers.get('CONTENT-LENGTH')
        env['CONTENT_LENGTH'] = int(content_len) if content_len else 0
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'HTTP'
        env['wsgi.input'] = data.input
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = True
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        [env.update({'HTTP_' + h.upper(): data.headers[h]}) for h in data.headers]
        
        close_conn = data.headers.get('CONNECTION')
        close_conn = True if close_conn is not None and close_conn.lower() == 'close' else False
        out = io.BytesIO()
        write = lambda obj: out.write(obj) if isinstance(obj, bytes) or isinstance(obj, bytearray) else out.write(str(obj).encode(self.encoding))
        outputs = []
        status = [200, 'OK']
        headers = {}
        def start_response(_status, _headers, exc_info=None):
            if _status is not None:
                _status = _status.strip()
                if len(_status) == 3:
                    _status = _status + ' '
                _status = _status.split(' ')
                status[0] = int(_status[0])
                status[1] = _status[1]
            if _headers is not None:
                [headers.update({h: _headers[h]}) for h in _headers]
            return write
        try:
            result = self.application(env, start_response)
            if result is not None:
                write(result)
        except Exception as e:
            logging.warn(e)
            traceback.print_exc()
            outputs.append(('%s 500 Internal Server Error\r\nConnection: close\r\n\r\n' % SERVER_PROTOCOL_VERSION).encode(self.encoding))
        else:
            outputs.append(('%s %d %s\r\n' % (SERVER_PROTOCOL_VERSION, status[0], status[1])).encode(self.encoding))
            for header in headers.items():
                if header[0] == 'Connection' and header[1].lower() == 'close':
                    close_conn = True
                    continue
                outputs.append(('%s: %s\r\n' % header).encode(self.encoding))
            if status[0] >= 300:
                close_conn = True
            if close_conn:
                outputs.append('Connection: close\r\n'.encode(self.encoding))
            content = out.getvalue()
            if content:
                content_len = len(content)
                if content_len:
                    if not 'Content-Length' in headers:
                        outputs.append(('Content-Length: %d\r\n\r\n' % content_len).encode(self.encoding))
                    outputs.append(content)
            else:
                outputs.append('\r\n'.encode(self.encoding))
        finally:
            for output in outputs:
                if output:
                    session.write(output)
            if close_conn:
                session.close()
    
    def connect(self, session):
        logging.info('处理客户端[%s:%d]链接' % session.client_address)
        session.recv_ready()
    def recv(self, session, data):
        logging.info('处理客户端[%s:%d]请求' % session.client_address)
        self.__process_data(session, data)
    def close(self, session):
        logging.info('处理客户端[%s:%d]关闭' % session.client_address)
        session.shutdown(socket.SHUT_RD)
        session.close()
    def hup(self, session):
        logging.info('处理客户端[%s:%d]强行关闭' % session.client_address)
    def error(self, session):
        logging.info('处理客户端[%s:%d]出错' % session.client_address)
