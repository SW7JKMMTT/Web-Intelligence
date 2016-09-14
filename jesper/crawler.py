#!/bin/env python
import concurrent.futures
import requests
from url_normalize import url_normalize
from datetime import datetime, timedelta
import queue
import heapq
import pprint

class Url(object):
    def __init__(self, url):
        self.url = url

    def str(self):
        return self.url

    def normalize(self):
        return url_normalize(self.url)

    def getHost(self):
        protocol, url = self.url.split("//", 1)
        host, path = url.split("/", 1)
        if host.startswith("www."):
            host = host[4:]
        return host

    def __str__(self):
        return "< URL: {} >".format(self.url)

class Host():
    def __init__(self, host):
        self.host = host
        self.urls = {}
        self.open = queue.Queue()
        self.nextOpen = datetime.now()
        self.isQueued = False

    def putWork(self, url):
        self.open.put(url)

    def getWork(self):
        return self.open.get_nowait()

    def empty(self):
        return self.open.empty();

    def __lt__(self, other):
        return self.nextOpen < other.nextOpen

    def __str__(self):
        return "< HOST: {}, ITEMS: {} >".format(self.host, self.open.qsize())

# Retrieve a single page and report the URL and contents
def load_url(url, host, timeout):
    r = requests.get(url, timeout=timeout)
    host.isQueued = False
    return r.content

class FrontQueue(object):
    def __init__(self):
        self.q = queue.Queue()

    def get(self):
        return self.q.get()

    def put(self, url):
        return self.q.put(url)

    def empty(self):
        return self.q.empty()

class BackQueue(object):
    def __init__(self, fq):
        self.bqs = {}
        self.bqh = queue.PriorityQueue()
        self.fq = fq

    def getHostQueue(self, host):
        return self.bqs[host]

    def _putHeap(self, bq):
        print("Putting {} on the heap".format(bq))
        self.bqh.put(bq)
        bq.isQueued = True

    def _getHeap(self):
        bq = self.bqh.get()
        if(bq.nextOpen > datetime.now()):
            self.bqh.put(bq)
            return None
        bq.isQueued = False
        return bq

    def _fillbq(self):
        while not self.fq.empty():
            w = self.fq.get()
            host = w.getHost()
            if not host in self.bqs:
                self.bqs[host] = Host(host)
            q = self.getHostQueue(w.getHost())
            q.putWork(w)
            if not q.isQueued:
                self._putHeap(q)

    def getNext(self):
        if self.bqh.empty():
            self._fillbq()

        q = self._getHeap()
        if q == None:
            return None, None
        work = q.getWork()

        if q.empty():
            self._fillbq()
        return work, q

    def done(self, host):
        if host.empty():
            return
        host.nextOpen = datetime.now() + timedelta(seconds=3)
        self._putHeap(host)

SEEDURLS = ['http://www.foxnews.com/',
        'http://www.cnn.com/',
        'http://europe.wsj.com/',
        'http://europe.wsj.com/',
        'http://europe.wsj.com/',
        'http://europe.wsj.com/',
        'http://www.bbc.co.uk/',
        'http://some-made-up-domain.com/']

fq = FrontQueue()

for url in SEEDURLS:
    u = Url(url)
    print("Adding seed {}".format(u))
    fq.put(u)
    # host = urlToHost(url)
    # hostRec = BackQueue(host)
    # hostRec.addWork(normalizeUrl(url))
    # BackQueues[host] = hostRec


sel = BackQueue(fq)
while True:
    w, h = sel.getNext()
    if w == None:
        continue
    print(w)
    sel.done(h)
