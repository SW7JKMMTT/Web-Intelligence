from urllib.parse import urlparse
import datetime
import time
import queue as q
import os

class Host(object):
    """Docstring for Host. """

    def __init__(self, host):
       self.host = host
       self.webpages = {}
       self.next_access = time.time()
       self.back_queue = q.Queue()


    def has_page(self, path):
        if path is '':
            path = '/'
        return path in self.webpages.keys()


    def add_page(self, webpage):
        path = '/'
        if not webpage.path is '':
            path = webpage.path
        self.webpages[path] = webpage
        dirname = os.path.dirname(path)[1:]
        file_path = os.path.join('./hosts/', self.host, dirname)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
	file_name = os.path.basename(path)
        if len(file_name) < 1:
            file_name = 'index.html'
        with open(os.path.join(file_path, file_name), 'w') as f:
            f.write(str(webpage.data))


    def __str__(self):
        return 'Host: {}, Pages {}, BQ {}'.format(self.host, len(self.webpages), self.back_queue.qsize())


    def __lt__(self, other):
        return self.next_access < other.next_access


    def __eq__(self, other):
        return self.next_access == other.next_access


class WebPage(object):
    """Docstring for WebPage. """

    def __init__(self, url=None, data=None, request=None, host=None):
        if request:
            url = request.url
            data = request.content
        self.url = url
        self.data = data
        self.host = host
        if host:
            host.add_page(self)
        self.crawled = datetime.datetime.now()


    @property
    def path(self):
        return urlparse(self.url).path

