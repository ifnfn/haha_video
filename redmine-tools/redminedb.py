from redmine import Redmine
import queue as Queue
import threading
import sys, os


def ioctl_GWINSZ(fd): #### TABULATION FUNCTIONS
    try: ### Discover terminal width
        import fcntl, termios, struct
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        return None
    return cr

def terminal_size():
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            env = os.environ
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)

    return int(cr[1]), int(cr[0])

class ProcessBar:
    def __init__(self, count=100, bar_word="=",lead=">"):
        self.num = 0
        self.count = count
        self.bar_word = bar_word
        self.lead = lead
        self.mutex = threading.Lock()

    def run(self):
        self.mutex.acquire()
        w,_ = terminal_size()
        w = w - 10
        self.num += 1
        rate = float(self.num) / float(self.count)
        rate_num = int(rate * w)
        sys.stdout.write('\r%3d%% |' % (rate * 100))
        for _ in range(0, rate_num):
            sys.stdout.write(self.bar_word)
        if rate < 1:
            sys.stdout.write(self.lead)
            for _ in range(rate_num + 1, w):
                sys.stdout.write(' ')

        sys.stdout.write('|')
        sys.stdout.flush()
        self.mutex.release()


class WorkManager(object):
    def __init__(self, thread_num=2):
        self.work_queue = Queue.Queue()
        self.bar = ProcessBar(0)
        self.threads = []
        for _ in range(thread_num):
            self.threads.append(Work(self.work_queue, self.bar))

    def add_job(self, job):
        self.bar.count += 1
        self.work_queue.put(job)

    def wait_allcomplete(self):
        for item in self.threads:
            item.start()
        for item in self.threads:
            if item.isAlive():item.join()

class Work(threading.Thread):
    def __init__(self, work_queue, bar):
        super().__init__()
        self.work_queue = work_queue
        self.bar = bar

    def run(self):
        while True:
            try:
                job = self.work_queue.get(block=False)
                job.execute()
                self.bar.run()
                self.work_queue.task_done()
            except:
                break

class RedmineBase(Redmine):
    def __init__(self):
        #HOST = '192.168.110.254'
        HOST = 'git.nationalchip.com'
        REDMINE_BASE = 'http://' + HOST + '/redmine'
        KEY = '2aa29b01a3fd827d180efa3ecb5fb8cf19e2e542'
        super().__init__(REDMINE_BASE, key=KEY)

    def GetGroup(self, gid):
        return self.group.get(gid)
