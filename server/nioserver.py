import logging
import multiprocessing, threading
import collections, queue
import os, sys
import traceback
import select, socket

__all__ = ['Executor', 'PooledExecutor', 'NIOServer']
           
class Executor:
    
    def __init__(self, jobs):
        self.jobs = jobs
    
    def start(self):
        while True:
            try:
                callable, args, kwargs = self.jobs.get()
                callable(*args, **kwargs)
            except Exception as e:
                logging.error(e)
                traceback.print_exc()

class PooledExecutor:

    DEFAULT_NR_THREADS = 4
    
    def __init__(self, name='Handler-exec', nr_threads=DEFAULT_NR_THREADS):
        if nr_threads < 1:
            raise ValueError('参数[nr_threads]不能小于1')
        self.name = name
        self.nr_threads = nr_threads
        self.jobs = queue.Queue()
    
    def set_nr_threads(self, nr_threads):
        if nr_threads is None or nr_threads < 1:
            raise ValueError('参数[nr_threads]不能小于1')
        self.nr_threads = nr_threads
            
    def start(self):
        [threading.Thread(name='%s-%d' % (self.name, i), target=Executor(self.jobs).start).start() for i in range(self.nr_threads)]
    
    def execute(self, callable, *args, **kwargs):
        if callable is None:
            raise ValueError('参数[callable]不能为空')
        self.jobs.put((callable, args, kwargs))

class NIOServer:
    
    DEFAULT_ADDRESS = ('', 8000) # 默认监听地址
    DEFAULT_NR_PROCESSORS = multiprocessing.cpu_count() # IO处理进程数，默认为CPU的核数
    DEFAULT_LISTEN_BACKLOG = 5 # 默认服务端socket允许同时连接请求数
    DEFAULT_DECODE = lambda session, bytes: (bytes,) # 默认协议decode
    DEFAULT_EXECUTOR= PooledExecutor() # Handler Executor
    
    def __init__(self, address=DEFAULT_ADDRESS, nr_processors=DEFAULT_NR_PROCESSORS, listen_backlog=DEFAULT_LISTEN_BACKLOG, sockopts=(), decode=DEFAULT_DECODE, executor=DEFAULT_EXECUTOR, exec_nr_threads=None, handler=None):
        '''
        设置服务器参数
        '''
        self.set_address(address)
        self.set_nr_processors(nr_processors)
        self.set_listen_backlog(listen_backlog)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_sockopts(sockopts)
        self.set_decode(decode)
        self.set_executor(executor)
        if exec_nr_threads is not None:
            self.set_executor_nr_threads(exec_nr_threads)
        self.set_handler(handler)
    
    def set_address(self, address):
        if address is None:
            raise ValueError('参数[address]不能为空')
        logging.debug('设置服务器参数 address: [%s:%d]' % address)
        self.address = address

    def set_nr_processors(self, nr_processors):
        if nr_processors is None or nr_processors < 1:
            raise ValueError('参数[nr_processors]不能小于1')
        logging.debug('设置服务器参数 nr_processors: [%d]' % nr_processors)
        self.nr_processors = nr_processors

    def set_listen_backlog(self, listen_backlog):
        if listen_backlog is None or listen_backlog < 1:
            raise ValueError('参数[_listen_backlog]不能小于1')
        logging.debug('设置服务器参数 listen_backlog: [%d]' % listen_backlog)
        self.listen_backlog = listen_backlog

    def set_sockopt(self, level, name, val):
        '''
        必须在setup()方法之后调用
        '''
        logging.debug('设置服务器socket选项[%d, %s, %s]' % (level, name, str(val)))
        try:
            self.server_socket.setsockopt(level, name, val)
        except Exception:
            self.server_socket.close()
            self.server_socket = None
            raise

    def set_sockopts(self, sockopts):
        '''
        必须在setup()方法之后调用
        '''
        if sockopts:
            [self.set_sockopt(opt[0], opt[1], opt[2]) for opt in sockopts]

    def set_decode(self, decode):
        if decode is None:
            raise ValueError('参数[decode]不能为空')
        logging.debug('设置服务器协议解码器decode')
        self.decode = decode

    def set_executor(self, executor):
        if executor is None:
            raise ValueError('参数[executor]不能为空')
        logging.debug('设置服务器Executor')
        self.executor = executor

    def set_executor_nr_threads(self, executor_nr_threads):
        logging.debug('设置服务器默认executor线程数量[%d]' % executor_nr_threads)
        self.executor.set_nr_threads(executor_nr_threads)

    def set_handler(self, handler):
        '''
        IO处理回调接口，必须提供
        '''
        if handler is None:
            raise ValueError('参数[handler]不能为空')
        logging.debug('设置服务器IO处理回调接口')
        self.handler = handler

    def daemonize(self):
        '''
        标准的2次Fork变成Daemon进程，无需解释太多
        '''
        try:
            if os.fork() > 0:
                sys.exit(0)
        except Exception as e:
            logging.critical(e)
            traceback.print_exc()
            sys.exit(1)

        os.setsid()

        try:	
            if os.fork() > 0:
                sys.exit(0)
        except Exception as e:
            logging.critical(e)
            traceback.print_exc()
            sys.exit(1)

        os.chdir('/')
        os.umask(0x22) # 文件权限755
        # 重定向标准输入输出和错误
        # os.dup2(open('/dev/null', 'r').fileno(), sys.stdin.fileno())
        # os.dup2(open('/dev/null', 'a+').fileno(), sys.stdout.fileno())
        # os.dup2(open('/dev/null', 'a+').fileno(), sys.stderr.fileno())

    def start(self):
        logging.debug('服务开始启动...')
        self.server_socket.bind(self.address)
        self.server_socket.listen(self.listen_backlog)
        for i in range(self.nr_processors):
            try:
                if os.fork() == 0:
                    break
            except Exception as e:
                logging.error(e)
        else:
            logging.debug('服务启动完成，正在监听[%s:%d]' % self.address)
            while True:
                os.wait()
                logging.warn('检测到IO处理进程退出')
                # 检测到有IO处理子进程退出，立即Fork一个子IO处理进程
                if os.fork() == 0:
                    break
        self.executor.start()
        Poller(self).start()

POLL_READ = select.POLLIN | select.POLLPRI # 可读事件
POLL_WRITE = select.POLLOUT # 可写事件
POLL_ERROR = select.POLLERR | select.POLLHUP # 出错事件

EVENT_REGISTER = 1 # 注册描述符事件
EVENT_MODIFY = 2 # 修改描述符事件
EVENT_UNREGISTER = 3 # 取消描述符注册
EVENT_SHUT_RD = 4 # 关闭输入端
EVENT_SHUT_WR = 5 # 关闭输出端
EVENT_SHUT_RDWR = 6 # 关闭输入和输出端
EVENT_CLOSE = 7 # 关闭描述符

RECV_BUFFER_SIZE = 1024 # 每次接收字节数

class Session:
    
    def __init__(self, client_address, fd, poller):
        self.client_address = client_address
        self.write_queue = collections.deque()
        self.__fd = fd
        self.__poller = poller
        self.__events = 0
        self.__shut_rd = False
        self.__shut_wr = False
        self.__closed = False
        self.attributes = {}
        
    def recv_ready(self):
        '''
        准备接收数据
        '''
        if self.__shut_rd or self.__closed:
            raise Exception('客户端[%s:%d]输入已经关闭' % self.client_address)
        if not self.__events:
            self.__events |= POLL_READ
            self.__poller.request(self.__fd, EVENT_REGISTER, self.__events)
        elif not self.__events & POLL_READ == POLL_READ:
            self.__events |= POLL_READ
            self.__poller.request(self.__fd, EVENT_MODIFY, self.__events)
    
    def write(self, bytes):
        if self.__shut_wr or self.__closed:
            raise Exception('客户端[%s:%d]输出已经关闭' % self.client_address)
        logging.debug('向客户端[%s:%d]写数据' % self.client_address)
        self.write_queue.append(bytes)
        if not self.__events:
            self.__events |= POLL_WRITE
            self.__poller.request(self.__fd, EVENT_REGISTER, self.__events)
        elif not self.__events & POLL_WRITE == POLL_WRITE:
            self.__events |= POLL_WRITE
            self.__poller.request(self.__fd, EVENT_MODIFY, self.__events)
    
    def shutdown(self, how):
        if self.__closed:
            raise Exception('客户端[%s:%d]已经关闭' % self.client_address)
        orig_events = self.__events
        event = 0
        if how is socket.SHUT_RD:
            if self.__shut_rd:
                raise Exception('客户端[%s:%d]输入已经关闭' % self.client_address)
            logging.debug('关闭客户端[%s:%d]输入' % self.client_address)
            self.__events &= ~POLL_READ
            self.__shut_rd = True
            event = EVENT_SHUT_RD
        elif how is socket.SHUT_WR:
            if self.__shut_wr:
                raise Exception('客户端[%s:%d]输出已经关闭' % self.client_address)
            logging.debug('关闭客户端[%s:%d]输出' % self.client_address)
            self.__events &= ~POLL_WRITE
            self.__shut_wr = True
            event = EVENT_SHUT_WR
        elif how is socket.SHUT_RDWR:
            if self.__shut_rd or self.__shut_wr:
                raise Exception('客户端[%s:%d]输入和输出已经关闭' % self.client_address)
            logging.debug('关闭客户端[%s:%d]输入输出' % self.client_address)
            self.__events = 0
            self.__shut_rd = True
            self.__shut_wr = True
            event = EVENT_SHUT_RDWR
        if orig_events and not self.__events:
            self.__poller.request(self.__fd, EVENT_UNREGISTER)
        else:
            self.__poller.request(self.__fd, EVENT_MODIFY, self.__events)
        self.__poller.request(self.__fd, event)
    
    def close(self):
        if self.__closed:
            raise Exception('客户端[%s:%d]已经关闭' % self.client_address)
        logging.debug('关闭客户端[%s:%d]' % self.client_address)
        self.__closed = True
        if self.__events:
            self.__poller.request(self.__fd, EVENT_UNREGISTER)
        self.__events = 0
        self.__poller.request(self.__fd, EVENT_CLOSE)


class Poller:
    '''
    轮询客户端链接
    '''
    def __init__(self, server):
        self.__server = server
        self.__requests = queue.deque()
        self.__poller = select.poll()
        self.__connections = {}
        self.__sessions = {}
        self.__alive = False
    
    def request(self, fd, event, poll_events=None):
        logging.debug('提交异步请求[%d, %d, %s]' % (fd, event, str(poll_events)))
        self.__requests.append((fd, event, poll_events))
        
    def __do_request(self):
        '''
        处理Session提交的异步请求
        '''
        redo_requests = []
        while True:
            fd, event, poll_events = (None, None, None)
            try:
                fd, event, poll_events = self.__requests.popleft()
            except IndexError as e:
                break
            try:
                connection = self.__connections.get(fd)
                if not connection:
                    logging.warn('客户端描述符[%d]已被删除' % fd)
                    continue
                if event is EVENT_REGISTER:
                    logging.debug('注册描述符事件[%d:%d]' % (fd, POLL_ERROR | poll_events))
                    self.__poller.register(connection, POLL_ERROR | poll_events)
                    continue
                if event is EVENT_MODIFY:
                    logging.debug('修改描述符事件[%d:%d]' % (fd, POLL_ERROR | poll_events))
                    self.__poller.modify(connection, POLL_ERROR | poll_events)
                    continue
                if event is EVENT_UNREGISTER:
                    logging.debug('撤销描述符事件[%d]' % fd)
                    # 检查是否还有数据未发送
                    session = self.__sessions[fd]
                    if session.write_queue:
                        logging.debug('该描述符[%d]还有数据未发送，推迟执行' % fd)
                        redo_requests.append((fd, event, poll_events))
                        continue
                    self.__poller.unregister(connection)
                    continue
                if event is EVENT_SHUT_RD:
                    connection.shutdown(socket.SHUT_RD)
                    continue
                if event is EVENT_SHUT_WR:
                    logging.debug('关闭描述符[%d]输出' % fd)
                    # 检查是否还有数据未发送
                    session = self.__sessions[fd]
                    if session.write_queue:
                        logging.debug('该描述符[%d]还有数据未发送，推迟执行' % fd)
                        redo_requests.append((fd, event, poll_events))
                        continue
                    connection.shutdown(socket.SHUT_WR)
                    continue
                if event is EVENT_SHUT_RDWR:
                    logging.debug('关闭描述符[%d]输入和输出' % fd)
                    # 检查是否还有数据未发送
                    session = self.__sessions[fd]
                    if session.write_queue:
                        logging.debug('该描述符[%d]还有数据未发送，推迟执行' % fd)
                        redo_requests.append((fd, event, poll_events))
                        continue
                    connection.shutdown(socket.SHUT_RDWR)
                    continue
                if event is EVENT_CLOSE:
                    logging.debug('关闭描述符[%d]' % fd)
                    # 检查是否还有数据未发送
                    session = self.__sessions[fd]
                    if session.write_queue:
                        logging.debug('该描述符[%d]还有数据未发送，推迟执行' % fd)
                        redo_requests.append((fd, event, poll_events))
                        continue
                    connection.close()
                    del self.__connections[fd]
                    del self.__sessions[fd]
                    continue
                logging.warn('未知请求[%d]' % fd)
            except Exception as e:
                logging.warn(e)
                traceback.print_exc()
        self.__requests.extend(redo_requests)
        
    def __handle_server_event(self, event):
        '''
        服务端描述符事件 
        '''
        if event & (select.POLLIN | select.POLLPRI):
            connection, client_address = self.__server.server_socket.accept() # 新的链接
            logging.debug('[%s:%d]链接本服务器' % client_address)
            connection.setblocking(False)
            fileno = connection.fileno()
            self.__connections[fileno] = connection
            session = Session(client_address, fileno, self)
            self.__sessions[fileno] = session
            self.__server.executor.execute(self.__server.handler.connect, session) # 触发链接事件
        elif event & POLL_ERROR:
            # 服务端描述符发生错误
            logging.error('服务端描述符被挂起或发生错误')
            self.__alive = False
            self.__poller.unregister(self.__server.server_socket)
            self.__server.server_socket.close()
            
    def __handle_client_readable(self, connection, session):
        '''
        客户端可读
        '''
        logging.debug('读取客户端[%s:%d]发送的数据' % session.client_address)
        client_shut = False
        while True:
            try:
                bytes = connection.recv(RECV_BUFFER_SIZE)
                if bytes:
                    requests = self.__server.decode(session, bytes)
                    if requests:
                        for data in requests:
                            logging.info('接收到客户端[%s:%d]的完整请求' % session.client_address)
                            self.__server.executor.execute(self.__server.handler.recv, session, data) # 触发数据到达事件
                else:
                    client_shut = True
                    break
            except BlockingIOError:
                break
        if client_shut:
            logging.info('客户端[%s:%d]输出终止' % session.client_address)
            self.__poller.modify(connection, POLL_ERROR)
            self.__server.executor.execute(self.__server.handler.close, session) # 触发客户端关闭事件
    
    def __handle_client_writable(self, connection, session):
        '''
        客户端可写
        '''
        while True:
            bytes = None
            try:
                bytes = session.write_queue.popleft()
            except IndexError as e:
                break
            if bytes:
                logging.debug('向客户端[%s:%d]写数据' % session.client_address)
                nsent = connection.send(bytes)
                logging.debug('向客户端[%s:%d]写入[%d]字节' % (session.client_address[0], session.client_address[1], nsent))
                if nsent < len(bytes):
                    logging.debug('本次还有剩余字节未写入')
                    # 提出未发送的数据放回write_queue中
                    session.write_queue.appendleft(bytes[nsent:])
                    break
    
    def __handle_client_error(self, fd, connection, session):
        '''
        客户端错误
        '''
        logging.warning('客户端[%s:%d]发生错误' % session.client_address)
        self.__poller.unregister(connection)
        connection.close()
        self.__server.executor.execute(self.__server.handler.error, session) # 触发错误事件
        del self.__connections[fd]
        del self.__sessions[fd]
    
    def __handle_client_hup(self, fd, connection, session):
        '''
        客户端强行关闭
        '''
        logging.warning('客户端[%s:%d]强行关闭' % session.client_address)
        self.__poller.unregister(connection)
        connection.close()
        self.__server.executor.execute(self.__server.handler.hup, session) # 触发强行关闭事件
        del self.__connections[fd]
        del self.__sessions[fd]
    
    def __handle_client_event(self, fd, event):
        '''
        客户端描述符事件
        '''
        connection = self.__connections[fd]
        session = self.__sessions[fd]
        if event & (select.POLLIN | select.POLLPRI):
            # 可读
            self.__handle_client_readable(connection, session)
        elif event & select.POLLOUT:
            # 可写
            self.__handle_client_writable(connection, session)
        elif event & select.POLLERR:
            # 客户端错误
            self.__handle_client_error(fd, connection, session)
        elif event & select.POLLHUP:
            # 客户端挂起
            self.__handle_client_hup(fd, connection, session)
        
    def start(self):
        self.__poller.register(self.__server.server_socket, POLL_READ | POLL_ERROR)
        server_fileno = self.__server.server_socket.fileno()
        self.__alive = True
        while self.__alive:
            timeouts = None if not self.__connections else 0
            events = self.__poller.poll(timeouts)
            for fd, event in events:
                try:
                    if fd is server_fileno:
                        # 服务端事件
                        self.__handle_server_event(event)
                    else:
                        # 客户端事件
                        self.__handle_client_event(fd, event)
                except Exception as e:
                    logging.error(e)
                    traceback.print_exc()
            # 处理Session提交的异步请求
            self.__do_request()
