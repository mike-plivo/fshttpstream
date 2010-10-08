import datetime
import eventlet.queue

import fsevents


class HttpStreamClient(object):
  def __init__(self, addr, sock, params={}):
    self.addr = addr
    self.sock = sock    
    self.queue = eventlet.queue.LightQueue()
    self.started = datetime.datetime.now()
    self.filters = set()
    for k, v in params.iteritems():
      self.filters.add((k, v))

  def accept_event(self, ev):
    for f in self.filters:
      try: 
        head, val = f
        if ev.dict_event[head] == val:
          return True
      except:
        pass 
    return False

  def get_duration(self):
    return (datetime.datetime.now()-self.started).seconds

  def send_event(self, ev):
    return self.sock.send(ev.event + fsevents.EVENT_EOL)

  def get_event(self):
    return self.queue.get_nowait()


