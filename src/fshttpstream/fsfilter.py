import re


class EventFilter(object):
    def __init__(self, events=['ALL'], filters=[]):
        self.__events = events
        self.__filters = filters

    def add_filter(self, var, val):
        self.__filters.append(var, val)

    def get_events(self):
        return " ".join(self.__events)

    def get_filters(self):
        return [ "%s %s" % (f[0], f[1]) for f in self.__filters ]


class ClientFilter(object):
    def __init__(self):
        self.__filters = set()

    def add_filter(self, regexp):
        if not regexp:
          return False
        try:
            self.__filters.add(re.compile(regexp, re.DOTALL|re.MULTILINE))
            return True
        except re.error:
            return False

    def __setitem__(self, regexp):
        return self.add_filter(regexp)

    def __str__(self):
        if not self.__filters:
            return "<ClientFilter no filter>"
        patterns = ", ".join(["'%s'" % reg.pattern for reg in self.__filters])
        return "<ClientFilter (%s)>" % str(patterns)

    def event_match(self, ev):
        # if not filter just return True =)
        if not self.__filters:
            return True
        # check matching
        for reg in self.__filters:
            if reg.search(ev.get_raw()):
                return reg
        return False

