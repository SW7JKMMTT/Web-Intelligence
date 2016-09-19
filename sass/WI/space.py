import queue as q
from hosts_n_pages import *
import r2d2
from urllib.parse import urlparse
import time

class FinalFrontier(object):

    def __init__(self):
        self.front_queue = q.Queue()
        self.hosts = dict()
        self.heap = q.PriorityQueue()


    def get(self):
        if self.heap.empty():
            print('Heap is empty! Front Queue size', self.front_queue.qsize() )
            self.__to_heap()
        return self.heap.get()


    def done(self, host):
        if host.back_queue.empty():
            self.__to_heap(max_puts=100)
        else:
            host.next_access = time.time() + r2d2.crawl_delay(host.host)
            self.heap.put(host)


    def __to_heap(self, max_puts=None):
        added = 0
        while not self.front_queue.empty() and (added < max_puts if max_puts else True):
            url = self.front_queue.get()
            host_name = urlparse(url).netloc
            if not host_name in self.hosts.keys():
                new_host = Host(host_name)
                self.hosts[host_name] = new_host
            host = self.hosts[host_name]
            if host.back_queue.empty():
                self.heap.put(host)
            host.back_queue.put(url)
            added += 1


    def get_host(self, host_name):
        if not host_name in self.hosts.keys():
            self.hosts[host_name] = Host(host_name)
        return self.hosts[host_name]


    def __str__(self):
        return 'Front Queue {} | Hosts: {} | Heap: {}'.format(self.front_queue.qsize(), len(self.hosts), self.heap.qsize())
