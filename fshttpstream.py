import eventlet
import eventlet.green.socket as socket
import eventlet.green.urllib as urllib
import eventlet.timeout
import eventlet.queue
import traceback
import sys
import time
import uuid
import datetime
import cgi
from urlparse import urlparse

import fslogger 
import fsevents
import fsclients



EOL = '\n\n'
EOL2 = '\r\n\r\n'
MAXLINES = 40
CHECKINACTIVITY = 30

class FreeswitchEventServer(object):
  def __init__(self, httphost, httpport, fshost, fsport, fspw, eventfilter='all', filters=(), logger=None, eventclass=fsevents.Event):
    self.httphost = httphost
    self.httpport = httpport
    self.fshost = fshost
    self.fsport = fsport
    self.fspw = fspw
    self._filter = 'event plain %s' % eventfilter
    self._filters = filters
    self.eventclass = eventclass
    if not logger:
      self.logger = fslogger.BaseLogger()
    else:
      self.logger = logger
    self.clients = {}
    self._eventd_thread = None

  def event_connect(self):
    while True:
      self.logger.debug("event connecting to %s %s:%d" % (self.fspw, self.fshost, self.fsport))
      self._cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self._cx.settimeout(20.0)
      timer = eventlet.timeout.Timeout(20.0)
      try:
        self._cx.connect((self.fshost, self.fsport))
        data = self._cx.recv(1024)
        self._cx.send('auth %s%s' % (self.fspw, EOL))
        data = ''
        while True:
          data += self._cx.recv(1)
          if data[-2:] == EOL:
            break
        if not 'Reply-Text: +OK accepted' in data:
          self._cx.close()
          self.logger.error("event auth failure")
          return False
        self.logger.info("event auth ok")
        res = self._set_filter()
        if res:
          self.logger.info("event connected")
          return res
      except eventlet.timeout.Timeout, te:  
        self.logger.error("event handler timeout")
      except socket.timeout, se:
        self.logger.error("event handler timeout")
      except socket.error, e:
        self.logger.error("event handler failure")
      finally:
        self._cx.settimeout(None)
        timer.cancel()
      eventlet.sleep(1.0)

  def _set_filter(self):
    # set main filter with format (plain)
    self._cx.send(self._filter + EOL)
    data = ''
    while True:
      data += self._cx.recv(1)
      if data[-2:] == EOL:
        break
      eventlet.sleep(0.001)
    if not 'Reply-Text: +OK' in data:
      self.logger.error("event filter failure (%s)" % self._filter)
      try: self._cx.close()
      except: pass
      return False
    else:
      self.logger.debug("%s" % self._filter)
    # set filters
    for fname, fvalue in self._filters:
      self._cx.send("filter %s %s%s" % (str(fname), str(fvalue), EOL))
      data = ''
      while True:
        data += self._cx.recv(1)
        if data[-2:] == EOL:
          break
        eventlet.sleep(0.001)
      if not 'Reply-Text: +OK' in data:
        self.logger.warn("event filter failure (filter %s %s)" % (str(fname), str(fvalue)))
      else:
        self.logger.debug("event filter %s %s" % (str(fname), str(fvalue)))
    self.logger.info("event filter ok")
    return True

  def event_handle(self):
    while True:
      ev = self._get_event()
      self.push_event(ev)
      eventlet.sleep(0.001)

  def _get_event(self):
    data = ''
    while True:
      try:
        data += self._cx.recv(1)
        if data[-2:] == EOL:
          if 'Event-Name:' in data:
            try:
              return self.eventclass(data)
            except Exception, e:
              self.logger.error(e.message)
          data = ''
        elif data == '':
          self.logger.warn("event handler error: buffer empty, fs probably down !")
          self.event_connect()
          data = ''
          continue
      except socket.error, e:
        self.logger.error("event handler error: %s" % e.message)
        self.event_connect()
        data = ''
        continue
      except socket.timeout, te:
        self.logger.error("event handler timeout")
        self.event_connect()
        data = ''
        continue

  def push_event(self, ev):
    for c in self.clients.values():
      try:
        self.logger.debug("push event %s to %s" % (ev.uuid, str(c.addr)))
        c.queue.put_nowait(ev)
      except eventlet.queue.Full:
        self.logger.warn("cannot put event %s to %s" % (ev.uuid, str(c.addr)))
      except Exception, e:
        self.logger.error("cannot put event %s to %s" % (ev.uuid, str(c.addr)))

  def httpd_start(self):
    try:
      self.logger.info("http start %s:%d" % (self.httphost, self.httpport))
      self.httpd_status = True
      self.httpdsock = eventlet.listen((self.httphost, self.httpport))
    except (KeyboardInterrupt, eventlet.StopServe):
      self.httpd_status = False
      raise
    eventlet.serve(self.httpdsock, self.http_handle)
    self.httpd_status = False

  def http_handle(self, sock, address):
    self.logger.info("http request start %s" % str(address))
    try:
      self.__http_handle(sock, address)
      self.logger.info("http request end %s" % str(address))
    except eventlet.StopServe:
      self.stop()
      raise eventlet.StopServe()
    except SystemExit:
      raise SystemExit()
    except socket.timeout:
      self.logger.error("http socket timeout %s" % str(address))
    except Exception, e:
      self.logger.error("http request failure %s: %s" % (str(address), e.message))
      [ self.logger.error(line) for line in traceback.format_exc().splitlines() ]
    return

  def __http_recv(self, sock):
    data = ''
    lines = 0
    maxbytes = MAXLINES*8192
    while lines < MAXLINES:
      try:
        c = sock.recv(1)
      except:
        return ''
      if c == '':
        return data
      data += c
      if len(data) >= maxbytes:
        return ''
      if c == '\n':
        lines += 1
      if data[-2:] in EOL:
        break
      elif data[-4:] in EOL2:
        break
    return data

  def __http_response(self, httpcode, info, msg='', contenttype='text/plain'):
    if msg: length = len(msg)
    else: length = -1
    resp = "HTTP/1.0 %s %s\r\n" % (str(httpcode), info)
    resp += "Date: %s\r\n" % (datetime.datetime.now().ctime())
    resp += "Server: fshttpstream\r\n"
    resp += "Expires: Sat, 1 Jan 2005 00:00:00\r\n";
    resp += "Last-Modified: %s\r\n" % (datetime.datetime.now().ctime())
    resp += "Cache-Control: no-cache, must-revalidate\r\n"
    resp += "Pragma: no-cache\r\n"
    if length > -1:
      resp += "Content-Type: %s\r\nContent-Length: %d\r\n\r\n" % (contenttype, length)
      resp += msg
    return resp

  def __http_parse_request(self, data):
    uri = data.split(' ')[1]
    uri = urlparse(uri)
    path = uri.path.rstrip('/')
    path = path.strip('/')
    path.strip()
    query = urllib.unquote_plus(uri.query)
    qdict = cgi.parse_qs(query)
    params = {}
    for k, v in qdict.iteritems():
      if v and isinstance(v, list): params[k] = v[0]
      elif v: params[k] = str(v)
    return (path, params)

  def __http_handle(self, sock, address):
    # set a global timeout for http request (20 sec)
    # if client request http stream, this timeout will be cancelled
    timer = eventlet.timeout.Timeout(20.0)
    try:
      # get data from client
      data = self.__http_recv(sock)  
      if not data[:3] == 'GET':
        self.logger.error("http bad data: abort for %s" % str(address))
        return

      # get path and query string from data
      path, params = self.__http_parse_request(data)
      self.logger.debug("http request for %s => path '%s'" % (str(address), str(path)))
      self.logger.debug("http request for %s => qs %s" % (str(address), str(params)))

      # status : show clients connected and close connection
      if path == 'status':
        self.logger.info("http status for %s" % str(address))
        msg = 'Clients: %d%s' % (len(self.clients), EOL)
        for c in self.clients.values():
          msg += "%s (since %s sec)%s" % (str(c.addr), c.get_duration(), EOL)
        msg = self.__http_response(200, 'status', msg)
        sock.send(msg)
        return
      # create new http stream client
      else:
        c = self._add_client(address, sock, params)
    except eventlet.timeout.Timeout:
      self.logger.error("http timeout getting data for %s" % str(address))
      return
    finally:
      timer.cancel()

    # update last event time 
    last_event_t = datetime.datetime.now()

    # send ready response
    ready = self.__http_response(200, "OK")
    c.sock.send(ready+EOL)

    # clear/flush browser buffer
    try: c.send_event(fsevents.FlushBufferEvent())
    except: pass

    while True:
      ev = None
      try:
        ev = c.get_event()
      except eventlet.queue.Empty:
        eventlet.sleep(0.01)
      except Exception, e:
        self.logger.warn("http get event failure for %s: %s" % (str(c.addr), e.message))
        eventlet.sleep(0.01)

      # check inactivity
      delta = (datetime.datetime.now()-last_event_t).seconds
      if delta > CHECKINACTIVITY:
        self.logger.debug("http inactivity sending ping to %s" % (str(c.addr)))
        ev = fsevents.PingEvent()
      if not ev:
        eventlet.sleep(0.01)
        continue
      # send event
      if ev:
        timer = eventlet.timeout.Timeout(5.0)
        try:
          if not isinstance(ev, fsevents.PingEvent):
            if c.accept_event(ev):
              self.logger.debug("http send event %s => %s: %s" % (str(c.addr), ev.uuid, str(ev.event)))
            else:
              self.logger.debug("http skip event %s => %s: %s" % (str(c.addr), ev.uuid, str(ev.event)))
              continue
          length1 = c.send_event(ev)
          last_event_t = datetime.datetime.now()
          if length1 == 0:
            self.logger.warn("http send nothing for %s: %s" % str(c.addr))
            self._remove_client(c.addr)
            return
        except eventlet.timeout.Timeout, te:
          self.logger.warn("http send event timeout reach for %s: %s" % (str(c.addr), te.message))
          self._remove_client(c.addr)
          return
        except socket.error, e1:
          self.logger.warn("http send event failure for %s: %s" % (str(c.addr), e1.message))
          self._remove_client(c.addr)
          return
        except socket.timeout, e2:
          self.logger.warn("http send event timeout for %s: %s" % (str(c.addr), e2.message))
          self._remove_client(c.addr)
          return
        except Exception, err:
          self.logger.error("http send event failure for %s: %s" % (str(c.addr), err.message))
          [ self.logger.error(line) for line in traceback.format_exc().splitlines() ]
          self._remove_client(c.addr)
          return
        finally:
          timer.cancel()

  def _add_client(self, address, sock, params):
    c = fsclients.HttpStreamClient(address, sock, params)
    self.clients[address] = c
    self.logger.debug("httpstream client %s added" % str(address))
    return c

  def _remove_client(self, address):
    try: self.clients[address].sock.close()
    except: pass
    try:
      del self.clients[address]
      self.logger.debug("httpstream client %s removed" % str(address))
    except KeyError, e:
      self.logger.warn("httpstream cannot remove client %s (not found)" % str(address))

  def eventd_start(self):
    if not self.event_connect():
      return
    self.event_handle()

  def start(self):
    self.logger.info("start")
    try:
      self._eventd_thread = eventlet.spawn(self.eventd_start)
      self.httpd_start()
    except KeyboardInterrupt:
      self.stop()
    
  def stop(self):
    self.logger.info("shutdown")
    if self._eventd_thread:
      self._eventd_thread.kill()
    sys.exit(1)



if __name__ == '__main__':
  fshost = '127.0.0.1'
  fsport = 8021
  fspassword = 'ClueCon'

  httphost = '0.0.0.0'
  httpport = 8000

  servicename = "fsexample"

  # set no filter when connecting to mod_event_socket (ie: event plain all)
  mainfilter = 'all'

  # no filter when connected
  fsfilters = ()

  # create logger (syslog)
  logger = fslogger.SysLogger(servicename=servicename)

  # create server
  server = FreeswitchEventServer(httphost, httpport, fshost, fsport, fspassword, 
                                 eventfilter=mainfilter, 
                                 filters=fsfilters,
                                 logger=logger,
                                 eventclass=fsevents.Event)
  # start server
  server.start()

