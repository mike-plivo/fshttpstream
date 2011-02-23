from fshttpstream import server

# freeswitch eventsocket host/port/password/event filter to connect to
FS_HOST = '127.0.0.1'
FS_PORT = 8021
FS_PASSWORD = 'ClueCon'
FS_FILTER = 'ALL'

# websocket listening host/port
WS_HOST = '0.0.0.0'
WS_PORT = 8000


myserver = server.Server(WS_HOST, WS_PORT, 
                         FS_HOST, FS_PORT, FS_PASSWORD, 
                         fsfilter=FS_FILTER)
myserver.start()
