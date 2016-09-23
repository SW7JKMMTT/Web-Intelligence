#!/usr/bin/env python3
import os
import concurrent.futures
import traceback
import urwid
import threading
import multiprocessing
from multiprocessing.managers import SyncManager
from multiprocessing import Queue
import time
import requests
import robots
from url_normalize import url_normalize
from datetime import datetime, timedelta
import urllib.parse
import urlspeed
import queue
import lxml.html
import cProfile
import event
import heapq
import pprint
import magic
from functools import singledispatch

class PageTooLargeError(Exception):
    def __init__(self, size = 0):
        self.size = size

class WrongTypeError(Exception):
    def __init__(self, t):
        self.type = t

class AbortError(Exception):
    pass


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
def save_queue(obj):
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
        return Url(urlspeed.urljoin(self.url, pa))

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

    def putVisited(self, url):
        self.urls[url.getPath()] = True

    def isVisited(self, url):
        return url.getPath() in self.urls.keys()

    def getRobots(self, url):
        if self.robots == None:
            try:
                roburl = url.join("/robots.txt")
                # print("Getting robots file {}".format(roburl.geturl()))
                content, size = downloadPage(url, 524288, {"text/plain", "text/html"}, 2)
            except WrongTypeError as e:
                # print(e.type)
                return None
            except (PageTooLargeError, AbortError):
                return None
            except (requests.exceptions.ReadTimeout, requests.exceptions.SSLError, requests.exceptions.TooManyRedirects, requests.exceptions.ConnectionError):
                return None
            try:
                self.robots = robots.compileRobots(content.decode())
            except UnicodeDecodeError:
                pass #I guess it wasn't unicode. Fuck it, i don't want to index them anyway
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

    def _getHost(self):
        if self.hosts.empty():
            return None
        host = self.hosts.get_nowait()
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
        # print("----Taking from main----")
        newHost = self.mq.getNext(self.cid)
        if newHost == None:
            return
        # print("New Host is: ", newHost)
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
        # print(host)
        if host == None:
            return None

        return host

    def done(self, host):
        host.nextOpen = datetime.now() + timedelta(seconds = 3)
        if host.hasWork():
            self._putHeap(host)
        else:
            self._fillbq()

MAX_PAGE_SIZE=20971520/2
def downloadPage(url, maxSize, allowedTypes, timeout):
    with requests.Session() as s:
        r = s.get(url.geturl(), timeout=timeout, stream=True)
        if "content-length" in r.headers and int(r.headers["content-length"]) >= maxSize:
            raise PageTooLargeError(int(r.headers["content-length"]))

        if "content-type" in r.headers and r.headers["content-type"] in allowedTypes:
            for t in allowedTypes:
                if r.headers["content-type"] == t or r.headers["content-type"].find(t):
                    break
            else:
                raise WrongTypeError(t)

        pageSize = 0
        data = bytes()
        first = True
        for chunk in r.iter_content(chunk_size=4096, decode_unicode=False):
            if not running.value:
                raise AbortError()

            pageSize += len(chunk)
            data += chunk

            if first:
                first = False
                guessedType = magic.from_buffer(data, mime=True)
                if guessedType not in allowedTypes:
                    raise WrongTypeError(guessedType)

            if pageSize > maxSize:
                raise PageTooLargeError()

        return data, pageSize

def parsePage(url, data, size):
    root = lxml.html.fromstring(data)
    links = []
    for link in root.xpath("//a[@href]"):
        loc = link.get("href").strip(" ")
        if loc == None:
            continue
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
def load_url(events, queue, url, host, timeout):
    if host.isVisited(url):
        return None
    rob = host.getRobots(url)
    if rob != None and not rob.isAllowed(url.getPath()):
        return UnparsablePage(url)
    try:
        events.downloading()
        content, size = downloadPage(url, MAX_PAGE_SIZE, {"text/html"}, timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects, requests.exceptions.ReadTimeout):
        # print("Read timed out")
        return UnparsablePage(url)
    except PageTooLargeError as p:
        return LargePage(url, p.size)
    except WrongTypeError as e:
        return UnparsablePage(url)
    events.parsing()
    page = parsePage(url, content, size)
    events.extracting()
    for l in page.getLinks():
        queue.discover(l)
    return page

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
    # print("You can't save {}".format(type(obj)))
    pass

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
events = event.EventQueue()

sel.discover([Url(url) for url in SEEDURLS])

def arun(eclient):
    try:
        eclient.starting()
        cq = ClientQueue(sel)
        while running.value:
            eclient.retrieving()
            h = cq.getNext()
            if h == None:
                continue
            assert(h.hasWork())
            w = h.getWork()
            page = load_url(eclient, cq, w, h, 2)
            if page != None:
                h.putVisited(w)
                updated.put(page)
                eclient.processed()
            cq.done(h)
        eclient.done()
    except AbortError:
        eclient.done()
    except Exception as e:
        eclient.exception()
        with open("error.log", "a") as f:
            traceback.print_exc(file=f)


def real_run(eclient):
    # print("Starting {}".format(i))
    try:
        # cProfile.runctx('arun(eclient)', globals(), locals(), filename="runner" + str(i) + ".stats")
        arun(eclient)
    except AbortError as e:
        eclient.exception()
        pass

def writequeue():
    os.makedirs("Back/hosts", exist_ok=True)
    while updated.qsize() > 0 or running.value:
        v = updated.get()
        os.makedirs("Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"), exist_ok=True)
        todisk(save(v), "Back/hosts/{}/urls/{}".format(v.url.getHost(), v.url.getPath().strip("/") or "darude"))


crawlerThreads = []
writerThreads = []
for i in range(20):
    eclient = events.connect()
    t = multiprocessing.Process(target=real_run, args=[eclient])
    t.start()
    crawlerThreads.append(t)

for i in range(2):
    t = multiprocessing.Process(target=writequeue)
    t.start()
    writerThreads.append(t)

def exit_on_q(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    elif key in ("s", "S"):
        running.value = False

processedPages = 0
def crawlEvent():
    global processedPages
    while events.hasEvents():
        e = events.get()
        if e.getEventType() == event.EventType.status:
            crawlers[e.i].set_text(e.getText())
            if e.getText() == "Done": #TODO: Not string compar
                crawler_wrap[e.i].set_attr_map({None: "crawlerdonebg"})
            else:
                crawler_wrap[e.i].set_attr_map({None: "crawlerbg"})
        if e.getEventType() == event.EventType.processed:
            processedPages += 1
            bottom_items[0].set_text("Processed: {}".format(processedPages))

            #This also means an update to the work queue
            bottom_items[1].set_text("Pending Write: {}".format(updated.qsize()))

        if e.getEventType() == event.EventType.error:
            crawlers[e.i].set_text("DEAD")
            crawler_wrap[e.i].set_attr_map({None: "crawlerdeadbg"})
try:

    palette = [
        ('crawlerbg',     'black', 'light gray'),
        ('crawlerdonebg', 'black', 'light blue'),
        ('crawlerdeadbg', 'black', 'light red'),
        ('crawlerAreabg', 'black', 'dark gray'),
        ('statusbar',     'black', 'dark gray'),
        ('bg',            'black', 'black'),]

    crawlers = [urwid.Text("Idle", align="center") for crawl in crawlerThreads]
    crawler_wrap = [urwid.AttrMap(urwid.Padding(crawl, width=20), "crawlerbg") for crawl in crawlers]
    crawler_area = urwid.AttrMap(urwid.Padding(urwid.GridFlow(crawler_wrap, 20, 3, 1, 'center'), left=4, right=3, min_width=15), 'crawlerAreabg')

    bottom_items = [urwid.Text("Starting"), urwid.Text("Starting")]
    bottom_col = urwid.AttrMap(urwid.Columns(bottom_items, 2), "statusbar")

    fill = urwid.Frame(urwid.Filler(crawler_area), footer=bottom_col)
    map2 = urwid.AttrMap(fill, 'bg')
    loop = urwid.MainLoop(map2, palette, unhandled_input=exit_on_q)
    loop.watch_file(events.getfd(), crawlEvent)
    loop.run()
    # time.sleep(timedelta(seconds=30).seconds)
except KeyboardInterrupt:
    print("Stopping")
running.value = False

#Since We stop the writing threads at the same time as the crawler threads we need to discard the last pages the crawler threads might produce
while updated.qsize() > 0:
    updated.get()

for k, thread in enumerate(crawlerThreads):
    thread.join()
for k, thread in enumerate(writerThreads):
    thread.join()
exit(0)
