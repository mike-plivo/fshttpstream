import os
import sys
import pwd
import grp

def user2uid(user):
    return int(pwd.getpwnam(user)[2])

def grp2gid(group):
    return int(grp.getgrnam(group)[2])

def get_uid():
    return os.getuid()

def get_gid():
    return os.getgid()

def do_foreground(uid, gid, serverpath):
    '''do_foreground()
    Set user, group, ...'''
    os.setgid(gid)
    os.setuid(uid)
    os.chdir(serverpath)

def do_daemon(uid, gid, serverpath=None, pidfile=None):
    '''do_daemon() -> bool
    Daemonize current process'''
    if not serverpath: serverpath = './'
    if not pidfile: pidfile = '/tmp/fshttpstream.pid'
    try:
        pid = os.fork()
    except Exception, err:
        print "Error : "+str(err)
        return False
    if pid == 0:
        os.setsid()
        try:
            pid = os.fork()
        except Exception, err:
            print "Error : "+str(err)
            return False
        if pid == 0:
            os.chdir(serverpath)
            os.umask(0)
            open(pidfile, "w").write(str(os.getpid()))
        else:
            os._exit(0)
    else:
        os._exit(0)
    os.setgid(gid)
    os.setuid(uid)
    sys.stdout = sys.stderr = open(os.devnull, 'a+')
