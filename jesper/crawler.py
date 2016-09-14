#!/bin/env python
import concurrent.futures
import requests
from url_normalize import url_normalize
from datetime import datetime

class HostRecord():
    def __init__(self):
        self.urls = {}
        self.open = []
        self.nextOpen = datetime.now
        self.isQueued = False

    def addWork(self, url):
        self.open.append(url)

    def popWork(self):
        return self.open.pop()

    def hasWork(self):
        return not self.open;

BackQueues = {}

def normalizeUrl(url):
    return url_normalize(url)

def urlToHost(url):
    protocol, url = url.split("//", 1)
    host, path = url.split("/", 1)
    if host.startswith("www."):
        host = host[4:]
    return host

SEEDURLS = ['http://www.foxnews.com/',
        'http://www.cnn.com/',
        'http://europe.wsj.com/',
        'http://www.bbc.co.uk/',
        'http://some-made-up-domain.com/']

# Retrieve a single page and report the URL and contents
def load_url(url, host, timeout):
    r = requests.get(url, timeout=timeout)
    host.isQueued = False
    return r.content

# We can use a with statement to ensure threads are cleaned up promptly
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    # Start the load operations and mark each future with its URL
    for url in SEEDURLS:
        host = urlToHost(url)
        hostRec = HostRecord()
        hostRec.addWork(normalizeUrl(url))
        BackQueues[host] = hostRec

    while True:
        for host, bq in BackQueues.items():
            if bq.isQueued or not bq.hasWork():
                continue
            bq.isQueued = True

            work =  bq.popWork()
            future = executor.submit(load_url, work, bq, 60)
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))
            else:
                print('%r page is %d bytes' % (url, len(data)))
    future_to_url = {executor.submit(load_url, url, 60): url for url in SEEDURLS}
    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))
        else:
            print('%r page is %d bytes' % (url, len(data)))
