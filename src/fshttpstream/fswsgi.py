import gevent.monkey
gevent.monkey.patch_all()

import gevent.socket as socket
import gevent.queue
from gevent import pywsgi
from gevent.pywsgi import Input
#from geventwebsocket.websocket import WebSocket

import traceback
import mimetools
import signal
import datetime
import sys
import os
from urllib import quote
from urllib import unquote

import fslogger
import fsevents
import fsclients
import fstools


CHECK_INACTIVITY = 20


class WSGIHandler(pywsgi.WSGIHandler):
    protocol_version = 'HTTP/1.1'
    MessageClass = mimetools.Message
  
    def __init__(self, socket, address, server):
        pywsgi.WSGIHandler.__init__(self, socket, address, server)

    def get_environ(self):
        env = self.server.get_environ()
        env['REQUEST_METHOD'] = self.command
        env['SCRIPT_NAME'] = ''

        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''
        env['PATH_INFO'] = unquote(path)
        env['QUERY_STRING'] = query

        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader

        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        env['SERVER_PROTOCOL'] = 'HTTP/1.0'

        host, port = self.socket.getsockname()
        env['SERVER_NAME'] = host
        env['SERVER_PORT'] = str(port)
        env['REMOTE_ADDR'] = self.client_address[0]
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'

        for header in self.headers.headers:
            key, value = header.split(':', 1)
            key = key.replace('-', '_').upper()
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                value = value.strip()
                key = 'HTTP_' + key
                if key in env:
                    if 'COOKIE' in key:
                        env[key] += '; ' + value
                    else:
                        env[key] += ',' + value
                else:
                    env[key] = value

        if env.get('HTTP_EXPECT') == '100-continue':
            wfile = self.wfile
        else:
            wfile = None
        chunked = env.get('HTTP_TRANSFER_ENCODING', '').lower() == 'chunked'
        self.wsgi_input = Input(self.rfile, self.content_length, wfile=wfile, chunked_input=chunked)
        env['wsgi.input'] = self.wsgi_input
        env['gevent.socket'] = self.socket
        return env



class WSGIServer(pywsgi.WSGIServer):
    def __init__(self, listener, application=None, backlog=None, spawn='default', log='default', handler_class=None, environ=None, **ssl_args):
        pywsgi.WSGIServer.__init__(self, listener, application, backlog, spawn, log, handler_class, environ, **ssl_args)


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
        while not self.connector.start():
            gevent.sleep(2.0)
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
        try:
            self.http_server = WSGIServer(self.addr, self.handle, log=self.log, handler_class=WSGIHandler)
            self.http_server.serve_forever()
        except:
            self.status = False
            raise

#    def handle_websocket(self, environ, start_response):
#        sock = environ['gevent.socket']
#        rfile = environ['wsgi.input'].rfile
#        wfile = environ['wsgi.input'].wfile
#        ws = WebSocket(rfile, wfile, sock, environ)
#        client = fsclients.WebSocketClient(ws, environ)
#        self.clients.add(client)
#        self.log.info("client added %s (%s)" % (str(client), client.host))
#        self.log.info("client %s filter: %s" % (str(client.get_uuid()), str(client.get_filter())))
#        last_event = datetime.datetime.now()
#        try:
#            while self.status:
#                try:
#                    now = datetime.datetime.now()
#                    if (now-last_event).seconds >= CHECK_INACTIVITY:
#                        self.log.debug("ping client %s" % str(client))
#                        client.send(fsevents.PingEvent())
#                        last_event = now
#                        gevent.sleep(0.02)
#                        continue
#                    ev = client.get_event()
#                    last_event = datetime.datetime.now()
#                    client.send(ev)
#                except gevent.queue.Empty:
#                    gevent.sleep(0.02)
#                except socket.error, e:
#                    self.log.warn("client %s socket error: %s" % (str(client), str(e)))
#                    return
#                except Exception, err:
#                    self.log.error(err.message)
#                    [ self.log.error(line) for line in traceback.format_exc().splitlines() ]
#                    return
#        finally:
#            self.clients.remove(client)
#            self.log.info("client deleted %s (%s)" % (str(client), client.host))

    def handle_stream(self, environ, start_response):
        print "handle_stream"
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
        #if environ['PATH_INFO'] == '/websock':
        #    return self.handle_websocket(environ, start_response)
        # http stream :
        if environ['PATH_INFO'] == '/stream':
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

