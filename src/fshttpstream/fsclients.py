import gevent.monkey
gevent.monkey.patch_all()
import gevent.queue

try: from urlparse import parse_qs as parse_qs
except: from cgi import parse_qs as parse_qs
import urllib
import datetime
import uuid
import fsfilter


class Client(object):
    def __init__(self):
        self.started = datetime.datetime.now()
        self.host = ''
        self.uuid = str(uuid.uuid4())
        self.__filter = fsfilter.ClientFilter()
        self.__queue = gevent.queue.Queue()

    def get_filter(self):
        return self.__filter

    def get_event(self):
        ev =  self.__queue.get_nowait()
        if self.get_filter().event_match(ev):
            return ev
        raise gevent.queue.Empty

    def push_event(self, ev):
        return self.__queue.put_nowait(ev)

    def get_duration(self):
        return (datetime.datetime.now()-self.started).seconds

    def get_host(self):
        return self.host

    def get_uuid(self):
        return self.uuid

    def _parse_qs(self, environ):
        try:
            querystring = urllib.unquote_plus(environ['QUERY_STRING'])
        except KeyError:
            return {}
        return parse_qs(querystring)

    def _get_filters_from_qs(self, environ):
        qs = self._parse_qs(environ)
        if not qs:
            return ()
        try:
            filter = qs['filter']
            if isinstance(filter, str):
                return (filter,)
            elif isinstance(filter, list):
                return tuple(filter)
        except KeyError:
            return ()
        return {}


class WebSocketClient(Client):
    def __init__(self, ws, environ):
        Client.__init__(self)
        self.__ws = ws
        self.__environ = environ
        self.host = self.__environ['REMOTE_ADDR']
        filters = self._get_filters_from_qs(self.__environ)
        for f in filters:
            self.get_filter().add_filter(f)

    def __str__(self):
        return 'WebSocketClient ' + self.uuid

    def send(self, msg):
        return self.__ws.send(msg.get_json())


class HttpStreamClient(Client):
    EOL = '\r\n\r\n'

    def __init__(self, environ):
        Client.__init__(self)
        self.__environ = environ
        self.__sock = self.__environ['gevent.socket']
        self.__sockfd = self.__sock.makefile()
        self.host = self.__environ['REMOTE_ADDR']
        filters = self._get_filters_from_qs(self.__environ)
        for f in filters:
            self.get_filter().add_filter(f)
        self.__send_headers()

    def __str__(self):
        return 'HttpStreamClient ' + self.uuid

    def send(self, msg):
        self.__sockfd.write(msg.get_json() + self.EOL)
        self.__sockfd.flush()

    def __send_headers(self):
        self.__sockfd.write('"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: -1\r\nDate: Tue, 01 Jan 1970 00:00:00 GMT\r\nConnection: keep-alive\r\nPragma: no-cache\r\n\r\n')
        self.__sockfd.flush()

