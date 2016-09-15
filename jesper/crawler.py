#!/bin/env python
import concurrent.futures
import requests
import bs4
import robots
from url_normalize import url_normalize
from datetime import datetime, timedelta
import urllib.parse
import queue
import heapq
import pprint

class Url(object):
    def __init__(self, url):
        self.url = urllib.parse.urlparse(url)

    def str(self):
        return self.url

    def normalize(self):
        url_normalize(self.url.geturl())

    def geturl(self):
        return self.url.geturl()

    def getHost(self):
        return self.url.netloc

    def getPath(self):
        return self.url.path

    def join(self, pa):
        return Url(urllib.parse.urljoin(self.url.geturl(), pa))

    def getProtocol(self):
        return self.url.scheme

    def __str__(self):
        return "< URL: {} >".format(self.url.geturl())

class Host():
    def __init__(self, host):
        self.host = host
        self.robots = None
        self.urls = {}
        self.open = queue.Queue()
        self.nextOpen = datetime.now()
        self.isQueued = False

    def putWork(self, url):
        self.open.put(url)

    def getWork(self):
        return self.open.get_nowait()

    def hasWork(self):
        return not self.open.empty();

    def getRobots(self, url):
        if self.robots == None:
            try:
                r = requests.get(url.join("robots.txt").geturl())
            except (requests.ConnectionError, requests.TooManyRedirects):
                return None
            self.robots = robots.compileRobots(r.text)
        return self.robots

    def __lt__(self, other):
        return self.nextOpen < other.nextOpen

    def __eq__(self, other):
        if not self is other:
            return False
        return self.nextOpen == other.nextOpen

    def __str__(self):
        return "< HOST: {}, ITEMS: {} >".format(self.host, self.open.qsize())

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
        print("Filling Queue")
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

        print("The queue is {}".format(self.bqh.qsize()))
        if not q.hasWork():
            self._fillbq()

        return work, q

    def done(self, host):
        host.nextOpen = datetime.now() + timedelta(seconds=3)
        if host.hasWork():
            self._putHeap(host)
        return

# Retrieve a single page and report the URL and contents
def load_url(fq, url, host, timeout):
    robloc = url.join("/robots.txt")
    rob = host.getRobots(url)
    if rob != None and rob.getPermission(url.getPath()) == robots.Permission.disallow:
        return
    print("Downloading {}".format(url.geturl()))
    try:
        h = requests.head(url.geturl(), timeout=timeout)
        print(h.headers["content-length"])
        r = requests.get(url.geturl(), timeout=timeout)
    except (requests.ReadTimeout, requests.ConnectionError, requests.TooManyRedirects):
        print("Read timed out")
        return
    print("Downloaded")
    bs = bs4.BeautifulSoup(r.content, "html.parser")
    for link in bs.find_all("a"):
        if not "href" in link.attrs:
            continue
        loc = link.attrs["href"].strip(" ")
        if loc == "":
            continue
        elif loc.startswith("mailto:"): #Fucking mail links
            continue
        elif loc[0] == "#": #It goes to some header
            continue
        elif loc.startswith("javascript"): #Kill me now
            continue
        else:
            newU = w.join(loc)
        if not newU.getProtocol().startswith("http"):
            return
        if not newU.getProtocol().startswith("http"):
            print("What is this?: {}".format(newU.geturl()))
        fq.put(newU)

SEEDURLS = [
        'http://dr.dk',
        'http://news.ycombinator.com',
        'http://informations-venner.dk',
    ]

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
    load_url(fq, w, h, 2)
    sel.done(h)
