import datetime
'''
import eventlet
import eventlet.green import time
from eventlet.wsgi import HttpProtocol as OriginalHttpProtocol
from eventlet.wsgi import _AlreadyHandled
from eventlet.wsgi import MINIMUM_CHUNK_SIZE
from eventlet.wsgi import format_date_time
from eventlet.wsgi import server as ev_server
from eventlet import websocket
from eventlet.green import os
from eventlet.green import socket
'''

import gevent.socket as socket
import gevent.monkey
import gevent.queue
from gevent import wsgi

import traceback
import signal
import sys
import os

import fslogger
import fsevents
import fsclients
import fstools

gevent.monkey.patch_all()

CHECK_INACTIVITY = 20

'''
# wrap eventlet.wsgi.server to ev_server
server = ev_server


class HttpProtocol(OriginalHttpProtocol):
    protocol_version = 'HTTP/1.1'
    minimum_chunk_size = MINIMUM_CHUNK_SIZE

    def handle_one_response(self):
        start = time.time()
        headers_set = []
        headers_sent = []

        wfile = self.wfile
        result = None
        use_chunked = [False]
        length = [0]
        status_code = [200]

        def write(data, _writelines=wfile.writelines):
            towrite = []
            if not headers_set:
                raise AssertionError("write() before start_response()")
            elif not headers_sent:
                status, response_headers = headers_set
                headers_sent.append(1)
                header_list = [header[0].lower() for header in response_headers]
                towrite.append('%s %s\r\n' % (self.protocol_version, status))
                for header in response_headers:
                    towrite.append('%s: %s\r\n' % header)

                # send Date header?
                if 'date' not in header_list:
                    towrite.append('Date: %s\r\n' % (format_date_time(time.time()),))

                client_conn = self.headers.get('Connection', '').lower()
                send_keep_alive = False
                if self.close_connection == 0 and \
                   self.server.keepalive and (client_conn == 'keep-alive' or \
                    (self.request_version == 'HTTP/1.1' and
                     not client_conn == 'close')):
                    # only send keep-alives back to clients that sent them,
                    # it's redundant for 1.1 connections
                    send_keep_alive = (client_conn == 'keep-alive')
                    self.close_connection = 0
                else:
                    self.close_connection = 1

                if 'content-length' not in header_list:
                    if self.request_version == 'HTTP/1.1':
                        use_chunked[0] = True
                        towrite.append('Transfer-Encoding: chunked\r\n')
                    elif 'content-length' not in header_list:
                        # client is 1.0 and therefore must read to EOF
                        self.close_connection = 1

                if self.close_connection:
                    towrite.append('Connection: close\r\n')
                elif send_keep_alive:
                    towrite.append('Connection: keep-alive\r\n')
                towrite.append('\r\n')
                # end of header writing

            if use_chunked[0]:
                ## Write the chunked encoding
                towrite.append("%x\r\n%s\r\n" % (len(data), data))
            else:
                towrite.append(data)
            try:
                _writelines(towrite)
                length[0] = length[0] + sum(map(len, towrite))
            except UnicodeEncodeError:
                self.server.log_message("Encountered non-ascii unicode while attempting to write wsgi response: %r" % [x for x in towrite if isinstance(x, unicode)])
                self.server.log_message(traceback.format_exc())
                _writelines(
                    ["HTTP/1.1 500 Internal Server Error\r\n",
                    "Connection: close\r\n",
                    "Content-type: text/plain\r\n",
                    "Content-length: 98\r\n",
                    "Date: %s\r\n" % format_date_time(time.time()),
                    "\r\n",
                    ("Internal Server Error: wsgi application passed "
                     "a unicode object to the server instead of a string.")])

        def start_response(status, response_headers, exc_info=None):
            status_code[0] = status.split()[0]
            if exc_info:
                try:
                    if headers_sent:
                        # Re-raise original exception if headers sent
                        raise exc_info[0], exc_info[1], exc_info[2]
                finally:
                    # Avoid dangling circular ref
                    exc_info = None

            capitalized_headers = [('-'.join([x.capitalize()
                                              for x in key.split('-')]), value)
                                   for key, value in response_headers]

            headers_set[:] = [status, capitalized_headers]
            return write

        try:
            try:
                result = self.application(self.environ, start_response)
                if (isinstance(result, _AlreadyHandled)
                    or isinstance(getattr(result, '_obj', None), _AlreadyHandled)):
                    self.close_connection = 1
                    return
                try:
                    if not headers_sent and hasattr(result, '__len__') and \
                            'Content-Length' not in [h for h, _v in headers_set[1]]:
                        headers_set[1].append(('Content-Length', str(sum(map(len, result)))))
                except IndexError:
                    # headers already sent in http stream, just close now
                    self.close_connection = 1
                    return
                towrite = []
                towrite_size = 0
                just_written_size = 0
                # if result is None, just close now
                if not result:
                    self.close_connection = 1
                    return
                for data in result:
                    towrite.append(data)
                    towrite_size += len(data)
                    if towrite_size >= self.minimum_chunk_size:
                        write(''.join(towrite))
                        towrite = []
                        just_written_size = towrite_size
                        towrite_size = 0
                if towrite:
                    just_written_size = towrite_size
                    write(''.join(towrite))
                if not headers_sent or (use_chunked[0] and just_written_size):
                    write('')
            except Exception:
                self.close_connection = 1
                exc = traceback.format_exc()
                self.server.log_message(exc)
                if not headers_set:
                    start_response("500 Internal Server Error",
                                   [('Content-type', 'text/plain'),
                                    ('Content-length', len(exc))])
                    write(exc)
        finally:
            if hasattr(result, 'close'):
                result.close()
            if (self.environ['eventlet.input'].chunked_input or
                    self.environ['eventlet.input'].position \
                    < self.environ['eventlet.input'].content_length):
                ## Read and discard body if there was no pending 100-continue
                if not self.environ['eventlet.input'].wfile:
                    while self.environ['eventlet.input'].read(MINIMUM_CHUNK_SIZE):
                        pass
            finish = time.time()

            for hook, args, kwargs in self.environ['eventlet.posthooks']:
                hook(self.environ, *args, **kwargs)

            self.server.log_message(self.server.log_format % dict(
                client_ip=self.get_client_ip(),
                date_time=self.log_date_time_string(),
                request_line=self.requestline,
                status_code=status_code[0],
                body_length=length[0],
                wall_seconds=finish - start))
'''


class Server(object):
    def __init__(self, host, port, fsconnector, log=None, docroot='./', 
                 daemon=False, pidfile=None, user=None, group=None):
        self.addr = (host, port)
        self.connector = fsconnector
        if not log: self.log = fslogger.BasicLogger()
        else: self.log = log
        self.status = False
        self.clients = set()
        self.docroot = docroot
        self.daemon = daemon
        self.pidfile = pidfile
        if not user: 
            self.uid = fstools.get_uid()
        else:
            self.uid = fstools.user2uid(user)
        if not group: 
            self.gid = fstools.get_gid()
        else:
            self.gid = fstools.grp2gid(group)
        self.__init_signals()

    def get_docroot(self):
        return self.docroot

    def handle_events(self):
        self.connector.set_logger(self.log)
        self.connector.start()
        while self.status:
            raw_event = self.connector.wait_event()
            self.__dispatch_events(raw_event)

    def __dispatch_events(self, raw_event):
        try:
            ev = fsevents.Event(raw_event)
            self.log.info("%s" % str(ev)) 
        except Exception, e:
            self.log.error(e.message)
        for c in self.clients:
            try:
                c.push_event(ev)
            except Exception, e:
                self.log.error(e.message)
                [ self.log.error(line) for line in traceback.format_exc().splitlines() ]

    def start(self):
        if self.daemon:
            fstools.do_daemon(self.uid, self.gid, self.docroot, self.pidfile)
        else:
            fstools.do_foreground(self.uid, self.gid, self.docroot)

        self.status = True

        try:
            gevent.spawn(self.handle_events)
        except:
            self.status = False
            raise


        self.log.info("http - start %s" % str(self.addr))
        server = wsgi.WSGIServer(self.addr, self.handle)
        server.serve_forever()
        '''
        try:
            self.log.info("http - start %s" % str(self.addr))
            self.sock = eventlet.listen(self.addr)
        except (KeyboardInterrupt, eventlet.StopServe):
            self.status = False
            raise
        server(self.sock, self.handle, protocol=HttpProtocol, log=self.log)
        '''
        self.status = False

    def handle_websocket(self, environ, start_response):
        wsock = websocket.WebSocketWSGI(self._handle_websocket)
        wsock(environ, start_response)

    def _handle_websocket(self, ws):
        client = fsclients.WebSocketClient(ws)
        self.clients.add(client)
        self.log.info("client added %s (%s)" % (str(client), client.host))
        self.log.info("client %s filter: %s" % (str(client.get_uuid()), str(client.get_filter())))
        last_event = datetime.datetime.now()
        try:
            while self.status:
                try:
                    now = datetime.datetime.now()
                    if (now-last_event).seconds >= CHECK_INACTIVITY:
                        self.log.debug("ping client %s" % str(client))
                        client.send(fsevents.PingEvent())
                        last_event = now
                        gevent.sleep(0.02)
                        continue
                    ev = client.get_event()
                    last_event = datetime.datetime.now()
                    client.send(ev)
                except gevent.queue.Empty:
                    gevent.sleep(0.02)
                except socket.error, e:
                    self.log.warn("client %s socket error: %s" % (str(client), str(e)))
                    return
                except Exception, err:
                    self.log.error(err.message)
                    [ self.log.error(line) for line in traceback.format_exc().splitlines() ]
                    return
        finally:
            self.clients.remove(client)
            self.log.info("client deleted %s (%s)" % (str(client), client.host))

    def handle_stream(self, environ, start_response):
        client = fsclients.HttpStreamClient(environ)
        self.clients.add(client)
        self.log.info("client added %s (%s)" % (str(client), client.host))
        self.log.info("client %s filter: %s" % (str(client.get_uuid()), str(client.get_filter())))
        last_event = datetime.datetime.now()
        do_flush = True
        try:
            while self.status:
                try:
                    now = datetime.datetime.now()
                    if do_flush:
                        self.log.debug("flush buffer client %s" % str(client))
                        # do a big flush =)
                        [ client.send(fsevents.FlushBufferEvent()) for x in range(20) ]
                        last_event = now
                        do_flush = False
                        gevent.sleep(0.02)
                        continue
                    if (now-last_event).seconds >= CHECK_INACTIVITY:
                        self.log.debug("ping client %s" % str(client))
                        client.send(fsevents.PingEvent())
                        last_event = now
                        gevent.sleep(0.02)
                        continue
                    ev = client.get_event()
                    last_event = datetime.datetime.now()
                    client.send(ev)
                except gevent.queue.Empty:
                    gevent.sleep(0.02)
                except socket.error, e:
                    self.log.warn("client %s socket error: %s" % (str(client), str(e)))
                    return
                except Exception, err:
                    self.log.error(err.message)
                    [ self.log.error(line) for line in traceback.format_exc().splitlines() ]
                    return
        finally:
            self.clients.remove(client)
            self.log.info("client deleted %s (%s)" % (str(client), client.host))

    def handle_status(self, environ, start_response):
        start_response('200 OK', [('content-type', 'text/plain')])
        page = 'Clients %d\r\n\r\n' % len(self.clients)
        page += '\r\n'.join([ '%s %s %s' % (str(c), str(c.get_host()), str(c.get_duration()))  for c in self.clients ])
        page += '\r\n\r\n'
        return [page]

    def handle(self, environ, start_response):
        # FIXME get/set ClientFilter from query string
        self.log.debug(str(environ))
        # websocket :
        if environ['PATH_INFO'] == '/websock':
            return self.handle_websocket(environ, start_response)
        # http stream :
        elif environ['PATH_INFO'] == '/stream':
            return self.handle_stream(environ, start_response)
        # http status :
        elif environ['PATH_INFO'] == '/status':
            return self.handle_status(environ, start_response)
        else:
            try:
                filepath = environ['PATH_INFO'].strip('/').strip()
                extension = filepath.split('.')[-1].strip()
                if extension == 'js': ctype = 'text/javascript'
                if extension == 'txt': ctype = 'text/plain'
                else: ctype = 'text/html'
                start_response('200 OK', [('content-type', ctype)])
                fpath = os.path.join(self.get_docroot(), filepath)
                return [open(fpath).read()]
            except IOError:
                start_response('404 Not Found', [('content-type', 'text/html')])
                return ["<h1>Not Found</h1>"]
            except:
                start_response('500 Internal server error', [('content-type', 'text/html')])
                [ self.log.warn(line) for line in traceback.format_exc().splitlines() ]
                return ["<h1>Internal server error</h1>"]

    def stop(self):
        sys.exit(0)

    def __init_signals(self):
        signal.signal(signal.SIGTERM, self.__sighandler)
        signal.signal(signal.SIGUSR1, self.__sighandler)
        signal.signal(signal.SIGUSR2, self.__sighandler)

    def __sighandler(self, signum, frame):
        if signum == signal.SIGTERM:
            self.log.warn("stopping now")
            self.stop()
        elif signum == signal.SIGUSR1:
            self.log.warn("set loglevel INFO")
            self.log.set_info()
        elif signum == signal.SIGUSR2:
            self.log.warn("set loglevel DEBUG")
            self.log.set_debug()

