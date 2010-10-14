import fshttpstream
<<<<<<< HEAD:examples/server.py
import fslogger
import fsevents
=======
import fsevents
import fslogger
>>>>>>> tmpbranch:examples/server.py

fshost = '127.0.0.1'
fsport = 8021
fspassword = 'ClueCon'

httphost = '0.0.0.0'
httpport = 8000

servicename = "fscallcenter"

mainfilter = 'CUSTOM callcenter::info'

fsfilters = (('CC-Action', 'member-queue-start'),
             ('CC-Action', 'members-count'),
             ('CC-Action', 'agent-state-change'),
             ('CC-Action', 'bridge-agent-start'),
             ('CC-Action', 'bridge-agent-end'),
             ('CC-Action', 'member-queue-end'))

# create logger
#logger = fslogger.SysLogger(servicename=servicename)
logger = fslogger.BaseLogger(servicename=servicename)

# create event handler
server = fshttpstream.FreeswitchEventServer(httphost, httpport, fshost, fsport, fspassword,
                                            eventfilter=mainfilter,
                                            filters=fsfilters,
                                            logger=logger,
                                            eventclass=fsevents.Event)
# start server
server.start()

