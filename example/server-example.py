import fshttpstream.fswsgi as fswsgi
import fshttpstream.fsconnector as fsconnector
import fshttpstream.fsfilter as fsfilter

# build event filter : ALL : no main event filter
filter = fsfilter.EventFilter(events=['ALL'], filters=[])

# create connector to freeswitch event socket
connector = fsconnector.EventConnector('127.0.0.1', 8021, 'ClueCon', filter)

# create server and start
server = fswsgi.Server('0.0.0.0', 8081, connector, docroot='./')
server.start()
