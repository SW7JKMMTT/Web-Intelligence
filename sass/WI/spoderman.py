#!/bin/python3
import r2d2
from space import FinalFrontier
from hosts_n_pages import WebPage
import requests
from contextlib import closing
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait, FIRST_COMPLETED
import queue as q
from urllib.parse import urlparse, urlunparse, urljoin
import time

num_crawler_workers = 20

user_agent = "spoderman"
header = { 'user-agent': user_agent }

seed_urls = [
        "http://reddit.com",
        "https://pornhub.com",
        "http://fbi.gov",
        "http://example.com",
        "https://change.org",
        "https://donaldjtrump.com"
]

scheme_whitelist = [
        "http",
        "https",
]

file_extensions_whitelist = [
        ".html",
        ".php",
        ".htm",
        ".asp",
        ".aspx"
]


def crawl_url(url):
    print('URL:', url)
    try:
        with requests.Session() as s:
            return s.get(url, timeout=2)
    except (requests.ConnectionError, requests.ReadTimeout, requests.TooManyRedirects):
        return None


def crawler(url_frontier):
    host = url_frontier.get()
    if host.next_access > time.time():
        print('Waiting', host.next_access - time.time())
        time.sleep(host.next_access - time.time())
    # print('Crawling from', host.host,  host.back_queue.qsize())
    url = host.back_queue.get()
    parsed_url = urlparse(url)
    if r2d2.is_allowed(url) and not host.has_page(parsed_url.path):
        req = crawl_url(url)
        if req:
            page = WebPage(request=req, host=host)

            for link in _links_from_webpage(page, url_frontier):
                url_frontier.front_queue.put(link)
        else:
            print('FAK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    else:
        print(url, 'not gunna visit that again' if host.has_page(parsed_url.path) else 'not allowed')
    url_frontier.done(host)

def _links_from_webpage(webpage, url_frontier):
    soup = BeautifulSoup(webpage.data, 'html.parser')
    dem_links = [ a_tag.get('href') for a_tag in soup.find_all('a') ]
    real_links = []
    for link in dem_links:
        link = urljoin(webpage.url, link)
        parsed_url = urlparse(link)
        link_host = url_frontier.get_host(parsed_url.netloc)
        sane_url = urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
        if _want_link(parsed_url.path):
            if (not sane_url in real_links) and (parsed_url.scheme in scheme_whitelist):
                real_links.append(sane_url)
    return real_links


def _want_link(path):
    page = path.split('/')[-1]
    if not ('.' in page) or any(file_extension in page for file_extension in file_extensions_whitelist):
        return True
    return False


def stats(f_q, b_q_heap, hosts):
    f, axarr = plt.subplots(2)
    plt.ion()
    plt.title('Stats')
    plt.ylabel('Num')
    return axarr


def update_stats(axarr, f_q, b_q_dict, hosts, crawled):
    bq_size = 0
    for bq in b_q_dict.values():
        bq_size += bq.qsize()
    host_list = [len(h.webpages) for h in hosts.values() if len(h.webpages) > 1 ]
    axarr[0].cla()
    axarr[0].set_xticks(range(5))
    axarr[0].set_xticklabels(['Front Queue', 'Comb. Back Queue', 'Hosts', 'Found Pages', 'Crawled Pages'], ha='left')
    axarr[0].bar(range(5), [f_q.qsize(), bq_size, len(hosts), sum(host_list), crawled])
    axarr[1].cla()
    axarr[1].bar(range(len(host_list)), host_list)
    axarr[1].set_xticks(range(len(host_list)))
    axarr[1].set_xticklabels(hosts, rotation=90, ha='center')
    plt.pause(0.1)


if __name__ == '__main__':
    url_frontier = FinalFrontier()

    for url in seed_urls:
        url_frontier.front_queue.put(url)

    should_cont = True
    with ThreadPoolExecutor(max_workers=num_crawler_workers + 1) as executor:
        crawled = 0
        while should_cont and crawled < 10:
            futures = { executor.submit(crawler, url_frontier) for i in range(num_crawler_workers) }
            crawled = num_crawler_workers
            try:
                while True:
                    futures = wait(futures, return_when=FIRST_COMPLETED)[1]
                    futures.add(executor.submit(crawler, url_frontier))
                    crawled += 1
            except KeyboardInterrupt:
                should_cont = False

