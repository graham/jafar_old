#!/usr/bin/env python

import os, errno
import sys, os, time, atexit
import signal
from signal import SIGTERM 
try:
    import setproctitle
except:
    setproctitle = None

try:
    os.mkdir('/tmp/pydaemons/')
except:
    pass

def pid_exists(pid):
    """Check whether pid exists in the current process table."""
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError, e:
        return e.errno == errno.EPERM
    else:
        return True

class Daemon:
    """
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin=None, stdout=None, stderr=None, proctitle=None):
        pidfile = pidfile.replace('/', '-')
        self.stdin = stdin or '/dev/null'
        self.stdout = stdout or '/tmp/pydaemons/' + pidfile + ".stdout"
        self.stderr = stderr or '/tmp/pydaemons/' + pidfile + ".stderr"
        self.pidfile = '/tmp/pydaemons/' + pidfile + ".pid"
        self.running = 1
        self.proctitle = proctitle
        self.attr = {}
        
        signal.signal(signal.SIGUSR1, self.handle_user_1)
        signal.signal(signal.SIGUSR2, self.handle_user_2)

    def soft_restart(self):
        self.delpid()
        self.start()
        
    def handle_user_1(self, *args, **kwargs):
        self.soft_restart()

    def handle_user_2(self, *args, **kwargs):
        self.soft_restart()

    def set_data(self, attr):
        self.attr = attr

    def status(self):
        if os.path.exists(self.pidfile):
            return pid_exists(int(open(self.pidfile).read().strip()))
        else:
            return False
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
    
        # decouple from parent environment
        #os.chdir("/") 
        #os.setsid() 
        #os.umask(700)
    
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
    
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
        if setproctitle:
            setproctitle.setproctitle(self.proctitle or ("daemon-%s" % self.pidfile))
    
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
            print 'not running yet...'
    
        if pid:
            if pid_exists(pid):
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            else:
                os.remove(self.pidfile)
        
        # Start the daemon
        self.daemonize()
        self._run()

    def stop(self):
        """
        Stop the daemon
        """
        self.log("stopping")
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
    
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            sys.exit(1)

    def log(self, message):
        print '%s: %s' % (time.asctime(), message)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass

    def _run(self):
        self.log("starting")
        self.pre_work()
        try:
            self.run()
        except Exception, e:
            import traceback
            traceback.print_exc()
            self.on_error(e)
        self.post_work()
        self.stop()

    def pre_work(self):
        pass
    def post_work(self):
        pass
    def on_error(self, error):
        pass


class DaemonWrapper(object):
    def __init__(self):
        self.script = ' '.join(sys.argv[1:-1])

    def handle(self):
        import sys
        d = Daemon('daemon-' + self.script)
        s = self.script
        def myrun():
            execfile(s)
        d.run = myrun

        if sys.argv[2] == 'start':
            d.start()
        elif sys.argv[2] == 'stop':
            d.stop()
        elif sys.argv[2] == 'restart':
            d.restart()
        elif sys.argv[2] == 'reload':
            pid = int(open(d.pidfile).read().strip())
            os.kill(pid, signal.SIGUSR1)
        elif sys.argv[2] == 'status' or sys.argv[2] == 'stat':
            print 'Currently running: ', d.status()
        else:
            print 'unknown command', sys.argv[2]

if __name__ == '__main__':
    x = DaemonWrapper()
    x.handle()
