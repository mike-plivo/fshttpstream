import eventlet
from eventlet.green import socket
import fslogger
import fsfilter


EOL = '\n\n'

class EventConnector(object):
    def __init__(self, host, port, password, filter=None, log=None):
        self.addr = (host, port)
        self.password = password
        if not filter: self.filter = fsfilter.EventFilter()
        else: self.filter = filter
        if not log: self.log = fslogger.BasicLogger()
        else: self.log = log

    def set_logger(self, log):
        self.log = log

    def start(self):
        return self.connect()

    def connect(self):
        self.log.info("fsconnector - connecting to %s %s" % (self.password, str(self.addr)))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(20.0)
        timer = eventlet.timeout.Timeout(20.0)
        try:
            self.sock.connect(self.addr)
            data = self.sock.recv(1024)
            if not self.__command('auth %s' % self.password):
                self.sock.close()
                self.log.error("fsconnector - auth failure")
                return False
            self.log.info("fsconnector - auth success")
            res = self.__set_filter()
            if res:
                self.log.info("fsconnector - connected")
                self.running = True
                return res
        except eventlet.timeout.Timeout, te:
            self.log.error("fsconnector - handler timeout")
        except socket.timeout, se:
            self.log.error("fsconnector - handler timeout")
        except socket.error, e:
            self.log.error("fsconnector - handler failure")
        finally:
            self.sock.settimeout(None)
            timer.cancel()
        return False

    def __set_filter(self):
        event_cmd = 'event plain %s' % (self.filter.get_events())
        if not self.__command(event_cmd):
            try: self.sock.close()
            except: pass
            return False
        for f in self.filter.get_filters():
            self.__command('filter '+f)
        return True

    def __command(self, msg):
        self.sock.send(msg+EOL)
        self.log.debug("fsconnector - command '%s'" % str(msg))
        data = ''
        while True:
            data += self.sock.recv(1)
            if data[-2:] == EOL:
                break
            else:
                eventlet.sleep(0.002)
        self.log.debug("fsconnector - %s" % str(data.splitlines()))
        if not 'Reply-Text: +OK' in data:
            self.log.warn("fsconnector - failure %s" % msg)
            return False
        self.log.debug("fsconnector - %s" % msg)
        return True

    def __get_event(self):
        data = ''
        while True:
            try:
                data += self.sock.recv(1)
                if data[-2:] == EOL:
                    return data
                elif data == '':
                    self.log.warn("fsconnector - handler error: buffer empty, fs probably down !")
                    return None
            except socket.error, e:
                self.log.error("fsconnector - handler error: %s" % e.message)
                return None
            except socket.timeout, te:
                self.log.error("fsconnector - handler timeout")
                return None

    def wait_event(self):
        raw_event = self.__get_event()
        if not raw_event:
            while not self.connect():
              eventlet.sleep(2.0)
        else:
            return raw_event
