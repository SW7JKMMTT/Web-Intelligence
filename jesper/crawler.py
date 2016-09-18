#!/bin/env python
import concurrent.futures
import threading
import time
import requests
import bs4
import robots
from url_normalize import url_normalize
from datetime import datetime, timedelta
import urllib.parse
import queue
import heapq
import pprint
from singledispatch import singledispatch

class CantStoreTypeError(Exception):
    def __init__(self, t):
        self.t = t

    def __str__(self):
        return str(self.t)

@singledispatch
def save(obj):
    raise CantStoreTypeError(type(obj))

@save.register(dict)
def save_dict(obj):
    this = {}
    for k, v in obj.items():
        this[k] = save(v)
    return this

@save.register(str)
def save_str(obj):
    return obj

@save.register(datetime)
def save_datetime(obj):
    return str(obj.timestamp())

#This is really expensive
@save.register(queue.Queue)
def save_datetime(obj):
    q = []
    while not obj.empty():
        i = obj.get_nowait()
        q.append(i)
    for k, i in enumerate(q):
        obj.put_nowait(i)
        q[k] = save(i)
    return q

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

@save.register(Url)
def save_url(obj):
    return obj.geturl()


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

    def putVisited(self, page):
        self.urls[page.getPath()] = page

    def isVisited(self, url):
        return url.getPath() in self.urls

    def getRobots(self, url):
        if self.robots == None:
            try:
                print("Getting robots file {}".format(url.join("/robots.txt").geturl()))
                r = requests.get(url.join("/robots.txt").geturl(), allow_redirects=False, timeout=2)
            except (requests.ConnectionError, requests.TooManyRedirects, requests.ReadTimeout):
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

@save.register(Host)
def save_host(obj):
    this = {}
    this["host"] = save(obj.host)
    this["urls"] = save(obj.urls)
    this["open"] = save(obj.open)
    this["nextOpen"] = save(obj.nextOpen)
    return this

class WebPage(object):
    def __init__(self, url):
        self.url = url
        self.visit = datetime.now()

    def getPath(self):
        return self.url.getPath()

    def getLinks(self):
        raise NotImplementedError()

    def getSize(self):
        raise NotImplementedError()

class LargePage(WebPage):
    def __init__(self, url, size = 0):
        WebPage.__init__(self, url)
        self.size = size

    def getSize(self):
        return self.size

class UnparsablePage(WebPage):
    def __init__(self, url):
        WebPage.__init__(self, url)

class HTMLPage(WebPage):
    def __init__(self, url, content, size, links):
        WebPage.__init__(self, url)
        self.content = content
        self.size = size
        self.linksTo = links
        self.visited = True

    def isCrawled(self):
        return self.visited

    def setCrawled(self):
        self.visited = True

    def getLinks(self):
        return self.linksTo

    def getSize(self):
        return self.size

class FrontQueue(object):
    def __init__(self):
        self.q = queue.Queue()

    def get(self):
        return self.q.get()

    def put(self, url):
        return self.q.put(url)

    def empty(self):
        return self.q.empty()

lock = threading.Lock()
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
        lock.acquire()
        if self.bqh.empty():
            self._fillbq()

        q = self._getHeap()
        if q == None:
            lock.release()
            return None, None
        if not q.hasWork():
            lock.release()
            return None, None
        work = q.getWork()

        if not q.hasWork():
            self._fillbq()
        lock.release()
        return work, q

    def done(self, host):
        host.nextOpen = datetime.now() + timedelta(seconds=3)
        if host.hasWork():
            self._putHeap(host)
        return

class PageTooLargeError(Exception):
    def __init__(self, size = 0):
        self.size = size

class WrongTypeError(Exception):
    pass

MAX_PAGE_SIZE=20971520
def downloadPage(url, maxSize, allowedTypes, timeout):
    with requests.Session() as s:
        r = s.get(url.geturl(), timeout=timeout, stream=True)
        if "content-length" in r.headers and int(r.headers["content-length"]) >= maxSize:
            print("Headers reported the content to be {} bytes long".format(r.headers["content-length"]))
            raise PageTooLargeError(int(r.headers["content-length"]))

        if "content-type" in r.headers and r.headers["content-type"] in allowedTypes:
            for t in allowedTypes:
                if r.headers["content-type"] == t or r.headers["content-type"].find(t):
                    break
            else:
                print("Headers reported the content to be of type {}".format(r.headers["content-type"]))
                raise WrongTypeError()

        pageSize = 0
        data = bytes()
        for chunk in r.iter_content(chunk_size=8192, decode_unicode=False):
            pageSize += len(chunk)
            data += chunk
            if pageSize > maxSize:
                print("Page was too long to be indexed")
                raise PageTooLargeError()
        return data, pageSize

def getPage(url, timeout):
    try:
        data, pageSize = downloadPage(url, MAX_PAGE_SIZE, ["text/html"], timeout)
    except PageTooLargeError as e:
        return LargePage(url, e.size)
    except WrongTypeError as e:
        return UnparsablePage(url)

    bs = bs4.BeautifulSoup(data, "html.parser")
    links = []
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
        elif loc.startswith("javascript:"): #Kill me now
            continue
        else:
            newU = url.join(loc)
        if not newU.getProtocol().startswith("http"):
            continue
        if not newU.getProtocol().startswith("http"):
            print("What is this?: {}".format(newU.geturl()))
        links.append(newU)
    return HTMLPage(url, data, len(data), links)

# Retrieve a single page and report the URL and contents
def load_url(fq, url, host, timeout):
    if host.isVisited(url):
        print("Already visited")
        return None
    rob = host.getRobots(url)
    if rob != None and not rob.isAllowed(url.getPath()):
        return
    print("Downloading {}".format(url.geturl()))
    try:
        page = getPage(url, timeout)
        for l in page.getLinks():
            fq.put(l)
        return page
    except (requests.ReadTimeout, requests.ConnectionError, requests.TooManyRedirects):
        print("Read timed out")
        return WebPage(url)

SEEDURLS = [
        'http://dr.dk',
    ]

fq = FrontQueue()

for url in SEEDURLS:
    u = Url(url)
    print("Adding seed {}".format(u))
    fq.put(u)

sel = BackQueue(fq)

def run():
    while True:
        w, h = sel.getNext()
        if w == None:
            continue
        pprint.pprint(save(h))
        page = load_url(fq, w, h, 2)
        if page != None:
            h.putVisited(page)
        sel.done(h)

for i in range(1):
    t = threading.Thread(target=run)
    print("Starting {}".format(i))
    time.sleep(2)
    t.start()
