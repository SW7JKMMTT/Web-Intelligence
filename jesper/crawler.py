#!/usr/bin/env python3
import os
import concurrent.futures
import threading
import multiprocessing
from multiprocessing.managers import SyncManager
from multiprocessing import Queue
import time
import requests
import bs4
import robots
from url_normalize import url_normalize
from datetime import datetime, timedelta
import urllib.parse
import queue
import cProfile
import heapq
import pprint
from functools import singledispatch

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

@save.register(list)
def save_list(obj):
    l = []
    for v in obj:
        l.append(save(v))
    return l

@save.register(bytes)
def save_bytes(obj):
    return str(obj)

@save.register(int)
def save_bytes(obj):
    return str(obj)

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

    def __reduce__(self):
        return (Url, (self.geturl(),))

@save.register(Url)
def save_url(obj):
    return obj.geturl()


class Host():
    def __init__(self, host, urls={}, o=[]):
        self.host = host
        self.robots = None
        self.urls = urls
        self.open = queue.Queue()
        for i in o:
            self.open.put(i)
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

    def getVisited(self, path):
        return self.urls[path]

    def isVisited(self, url):
        return url.getPath() in self.urls.keys()

    def getRobots(self, url):
        if self.robots == None:
            try:
                roburl = url.join("/robots.txt")
                print("Getting robots file {}".format(roburl.geturl()))
                r = requests.get(roburl.geturl(), allow_redirects=False, timeout=2)
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
        return "< HOST: {}, ITEMS: {}, NEXTOPEN: {} >".format(self.host, self.open.qsize(), self.nextOpen)

    def __reduce__(self):
        t = [i for i in self.open.queue]
        return (Host, (self.host, self.urls, t))

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

    def __reduce__(self):
        return (WebPage, (self.url,))

class LargePage(WebPage):
    def __init__(self, url, size = 0):
        WebPage.__init__(self, url)
        self.size = size

    def getSize(self):
        return self.size

    def __reduce__(self):
        return (LargePage, (self.url, self.size, ))

@save.register(LargePage)
def save_largepage(obj):
    this = {}
    this["url"] = save(obj.url)
    this["size"] = save(obj.size)
    return this

class UnparsablePage(WebPage):
    def __init__(self, url):
        WebPage.__init__(self, url)

    def __reduce__(self):
        return (LargePage, (self.url, ))

@save.register(UnparsablePage)
def save_unparsablepage(obj):
    this = {}
    this["url"] = save(obj.url)
    return this

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

    def __reduce__(self):
        return (HTMLPage, (self.url, self.content, self.size, self.linksTo, ))

@save.register(HTMLPage)
def save_htmlpage(obj):
    this = {}
    this["content"] = save(obj.content)
    this["size"] = save(obj.size)
    this["linksTo"] = save(obj.linksTo)
    this["visited"] = save(obj.visited)
    return this


class FrontQueue(object):
    def __init__(self):
        self.q = queue.Queue()

    def get(self):
        return self.q.get()

    def put(self, url):
        return self.q.put(url)

    def empty(self):
        return self.q.empty()

class MainQueue(object):
    def __init__(self):
        self.hostnames = {}
        self.hostMap = {}
        self.hosts = queue.Queue()
        self.clients = []
        self.fqs = {}
        self.fq = []

    def connect(self):
        newIndex = len(self.clients)
        self.clients.insert(newIndex, True)
        self.fqs[newIndex] = []
        return newIndex

    def discover(self, newUrls):
        self.fq.extend(newUrls)

    def getFq(self, cid):
        return self.fqs[cid]

    def getHostQueue(self, host):
        return self.hostnames[host]

    def _putHost(self, bq):
        self.hosts.put(bq)
        bq.isQueued = True

    def _getHost(self):
        if self.hosts.empty():
            return None
        host = self.hosts.get_nowait()
        host.isQueued = False
        return host

    def _fillbq(self):
        tmpl = self.fq
        self.fq = []
        for w in tmpl:
            hostname = w.getHost()
            if hostname in self.hostMap:
                cowner = self.hostMap[hostname]
                self.fqs[cowner].append(w)
            else:
                if not hostname in self.hostnames:
                    self.hostnames[hostname] = Host(hostname)
                host = self.hostnames[hostname]
                host.putWork(w)
                if not host.isQueued:
                    self._putHost(host)

    def getNext(self, cid):
        if self.hosts.empty():
            self._fillbq()

        q = self._getHost()
        if q == None:
            return None

        self.hostMap[q.host] = cid

        return q

class ClientQueue(object):
    def __init__(self, mq):
        self.mq = mq
        self.fq = []
        self.myhosts = {}
        self.hostHeap = queue.PriorityQueue()
        self.cid = mq.connect()

    def discover(self, url):
        self.fq.append(url)

    def _putHeap(self, host):
        self.hostHeap.put(host)
        host.isQueued = True

    def _getHeap(self):
        if self.hostHeap.empty():
            return self._takeHost()
        host = self.hostHeap.get_nowait()
        host.isQueued = True
        if(host.nextOpen > datetime.now()):
            self.hostHeap.put_nowait(host)
            return self._takeHost()
        host.isQueued = False
        return host

    def _takeHost(self):
        print("----Taking from main----")
        newHost = self.mq.getNext(self.cid)
        if newHost == None:
            return
        print("New Host is: ", newHost)
        self.myhosts[newHost.host] = newHost
        return newHost

    def _fillbq(self):
        tmp = self.fq
        self.fq = []
        tmp.extend(self.mq.getFq(self.cid))
        unknown = []
        for url in tmp:
            hostname = url.getHost()
            if hostname in self.myhosts:
                host = self.myhosts[hostname]
                host.putWork(url)
                if not host.isQueued:
                    self._putHeap(host)
            else:
                unknown.append(url)
        self.mq.discover(unknown)

    def getNext(self):
        if self.hostHeap.empty():
            self._fillbq()

        host = self._getHeap()
        print(host)
        if host == None:
            return None

        return host

    def done(self, host):
        host.nextOpen = datetime.now() + timedelta(seconds = 3)
        if host.hasWork():
            self._putHeap(host)
        else:
            self._fillbq()

@save.register(MainQueue)
def save_bq(obj):
    this = {}
    this["hosts"] = {}
    for k, v in obj.bqs.items():
        this["hosts"][k] = save(v)
    return this

class PageTooLargeError(Exception):
    def __init__(self, size = 0):
        self.size = size

class WrongTypeError(Exception):
    pass

MAX_PAGE_SIZE=20971520/2
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

only_a_tags = bs4.SoupStrainer("a")
def getPage(url, data, size):
    bs = bs4.BeautifulSoup(data, "html.parser", parse_only=only_a_tags)
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

        newU = url.join(loc)
        if not newU.getProtocol().startswith("http"):
            continue
        links.append(newU)
    return HTMLPage(url, data, len(data), links)

# Retrieve a single page and report the URL and contents
def load_url(q, url, host, timeout):
    if host.isVisited(url):
        print("Already visited")
        return None
    rob = host.getRobots(url)
    if rob != None and not rob.isAllowed(url.getPath()):
        return UnparsablePage(url)
    print("Downloading {}".format(url.geturl()))
    try:
        content, size = downloadPage(url, MAX_PAGE_SIZE, ["text/html"], timeout)
        page = getPage(url, content, size)
        for l in page.getLinks():
            q.discover(l)
        return page
    except (requests.ReadTimeout, requests.ConnectionError, requests.TooManyRedirects):
        print("Read timed out")
        return UnparsablePage(url)
    except PageTooLargeError as p:
        return LargePage(url, p.size)
    except WrongTypeError as e:
        return UnparsablePage(url)

SEEDURLS = [
        'https://pornhub.com',
        'http://fbi.gov',
        'http://example.com',
        'https://change.org',
        'https://donaldjtrump.com',
    ]

class MyManager(SyncManager):
    pass

def pathJoin(path, new):
    new = new.strip("/")
    if new == "":
        new = "darude"
    return os.path.join(path, new)

@singledispatch
def todisk(obj, path):
    print("You can't save {}".format(type(obj)))

@todisk.register(str)
def todisk_str(obj, path):
    with open(path, "w") as f:
        print(obj, file=f)

@todisk.register(list)
def todisk_list(obj, path):
    allStrs = all(type(o) == str for o in obj)
    if allStrs:
        with open(path, "w") as f:
            for v in obj:
                print(v, file=f)
    else:
        os.makedirs(path, exist_ok=True)
        for k, v in enumerate(obj):
            p = pathJoin(path, str(k))
            todisk(v, p)

@todisk.register(dict)
def todisk_dict(obj, path):
    os.makedirs(path, exist_ok=True)
    for k, v in obj.items():
        p = pathJoin(path, str(k))
        todisk(v, p)

MyManager.register("bq", MainQueue)
MyManager.register("up", queue.Queue)

def Manager():
    m = MyManager()
    m.start()
    return m

# fq = FrontQueue()
running = multiprocessing.Value("b", True)

m = Manager()
#updated = m.up()
updated = Queue()
sel = m.bq()

sel.discover([Url(url) for url in SEEDURLS])

def arun():
    cq = ClientQueue(sel)
    while running.value:
        h = cq.getNext()
        if h == None:
            continue
        assert(h.hasWork())
        w = h.getWork()
        page = load_url(cq, w, h, 2)
        if page != None:
            h.putVisited(page)
            updated.put(page)
        cq.done(h)

def real_run(i):
    print("Starting {}".format(i))
    # cProfile.runctx('arun()', globals(), locals(), filename="runner" + str(i) + ".stats")
    arun()
    return 0

th = []
for i in range(150):
    t = multiprocessing.Process(target=real_run, args=[i])
    t.start()
    th.append(t)

start = datetime.now()
try:
    os.makedirs("Back/hosts", exist_ok=True)
    while datetime.now() < start + timedelta(seconds=240):
        v = updated.get()
        print("-----Saving {}, {} to go".format(v, updated.qsize()))
        os.makedirs("Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"), exist_ok=True)
        host = sel.getHostQueue(v.url.getHost())
        todisk(save(v), "Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"))
        v.content = ""
except KeyboardInterrupt:
    print("Stopping")
print("--------------------------- [2 secs WARNING] -----------------------")
running.value = False
time.sleep(200)
while not updated.empty():
    print("---PREGET SIZE: {}".format(updated.qsize()))
    v = updated.get()
    print("-----Saving {}, {} to go".format(v, updated.qsize()))
    os.makedirs("Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"), exist_ok=True)
    host = sel.getHostQueue(v.url.getHost())
    todisk(save(v), "Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"))
    print("SAVED")
for k, thread in enumerate(th):
    print("Joined {}".format(k))
    thread.join()
exit(0)
