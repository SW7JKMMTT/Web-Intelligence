#!/bin/python3
from near_dup import near_dup_percentage
import r2d2
import requests as r
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import queue as q
from pprint import pprint
from data_store import *
from urllib.parse import urlparse
import threading
import time
import matplotlib.pyplot as plt

front_queue = q.Queue()
back_queues = {}
user_agent = "spoderman"
header = { 'user-agent': user_agent }
seed_urls = [
        "https://www.google.dk/",
        "http://www.npm.org/",
        "https://www.satai.dk/",
        "https://news.ycombinator.com/"
]

def crawl_url(url):
    print('URL:', url)
    try:
        return r.get(url, headers=header, timeout=5)
    except:
        pass
    return None

def put_it_in(url, front_queue=front_queue):
    if r2d2.is_allowed(url):
        front_queue.put(url)


def front_to_back():
    while True:
        req = crawl_url(front_queue.get())
        if req:
            page = WebPage(request=req)
            get_host(url=req.url).add_page(page)

            mah_q = None
            try:
                mah_q = back_queues[urlparse(req.url).netloc]
            except:
                mah_q = q.Queue()
                back_queues[urlparse(req.url).netloc] = mah_q
            for link in page.links:
                mah_q.put(link)


def back_to_front():
    while True:
        for bq in list(back_queues.values()):
            if bq.empty():
                continue
            url = bq.get()
            put_it_in(url)

def stats():
    f, axarr = plt.subplots(2)
    plt.ion()
    plt.title('Stats')
    while True:
        bq_size = 0
        for bq in list(back_queues.values()):
            bq_size += bq.qsize()
        axarr[0].bar(range(3), [front_queue.qsize(), bq_size, len(get_hosts())])
        host_list = [h for h in get_hosts().values() if len(h.webpages) > 1 ]
        axarr[1].bar(range(len(host_list)), [len(h.webpages) for h in host_list])
        axarr[1].xticks([h.host for h in host_list], range(len(host_list)))

        plt.pause(0.1)

def init_seed_data():
    for url in seed_urls:
        if r2d2.is_allowed(url):
            front_queue.put(url)


if __name__ == '__main__':
    init_seed_data()

    front_threads = []
    back_threads = []
    for i in range(1):
        f_t = threading.Thread(target=front_to_back)
        b_t = threading.Thread(target=back_to_front)
        front_threads.append(f_t)
        back_threads.append(b_t)
        f_t.start()
        b_t.start()

    stats()
        # for host, data in get_hosts().items():
        #     if len(data.webpages):
        #         print('Host:', host,'[', len(data.webpages),']')
