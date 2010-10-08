import datetime
import uuid
import urllib
try: import json
except ImportError: import simplejson as json


EVENT_EOL = '@@END@@'


class Event(object):
  def __init__(self, raw_event, flushbuffer=False):
    self._flush = flushbuffer
    self.uuid = str(uuid.uuid4())
    self.raw_event = raw_event
    self.dict_event = None 
    self.event = self.__event2json(raw_event)

  def __event2json(self, data):
    self.dict_event = {}
    if self._flush:
      l = len(data)
      bufferl = 1024-l
      if bufferl > 0: ev['Flush-Browser-Buffer'] = 'X'*bufferl
    for line in data.splitlines():
      if line and ': ' in line:
        var, val = line.split(': ', 1)
        var = var.strip()
        val = urllib.unquote_plus(val.strip())
        self.dict_event[var] = val
    return json.dumps(self.dict_event)


class PingEvent(Event):
  def __init__(self):
    Event.__init__(self, raw_event='Event-Name: Ping')


class FlushBufferEvent(Event):
  def __init__(self):
    Event.__init__(self, raw_event='Event-Name: FlushBuffer', flushbuffer=True)


