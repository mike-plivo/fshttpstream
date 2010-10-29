import fshttpstream.fswsgi as fswsgi
import fshttpstream.fsconnector as fsconnector
import fshttpstream.fsfilter as fsfilter

### filter events ###
# build event filter : ALL : no main event filter (see freeswitch mod_event )
filter = fsfilter.EventFilter(events=['ALL'], filters=[])

### connector to freeswitch server ###
# create connector to freeswitch event socket, 
connector = fsconnector.EventConnector('127.0.0.1', 8021, 'ClueCon', filter)



### examples for running server ####

# create server and start foreground, logging to stdout
server = fswsgi.Server('0.0.0.0', 8081, connector, docroot='./')
print dir(server.log)
server.start()



# create server and start daemon, logging to syslog
'''
# 1) - create logger
import fshttpstream.fslogger as fslogger
logger = fslogger.SysLogger()
# 2 - start server
server = fswsgi.Server('0.0.0.0', 8081, connector, log=logger, 
                       docroot='./', pidfile='/tmp/fshttpstream.pid', daemon=True)
server.start()
'''



# create server and start foreground, logging to stdout  with loglevel INFO
'''
import fshttpstream.fslogger as fslogger
logger = fslogger.BasicLogger(loglevel=fslogger.LOG_INFO)
# create server and start foreground, logging to stdout
server = fswsgi.Server('0.0.0.0', 8081, connector, docroot='./', log=logger)
server.start()
'''
