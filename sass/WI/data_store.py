from urllib.parse import urlparse, urljoin
import datetime
from bs4 import BeautifulSoup

visited = {}

def get_host(host=None, url=None):
    if url:
        host = urlparse(url).netloc
    try:
        return visited[host]
    except:
        return Host(host)

def get_hosts():
    return visited

class Host(object):

    """Docstring for Host. """

    def __init__(self, host):
       self.host = host
       self.webpages = {}
       visited[host] = self

    def has_page(self, path):
        return path in self.webpages.keys()

    def add_page(self, webpage):
        self.webpages[webpage.path] = webpage


def want(path):
    if path.endswith('http') or path.endswith('php') or path.endswith('htm'):
        return True
    return False


class WebPage(object):

    """Docstring for WebPage. """

    def __init__(self, url=None, data=None, request=None):
        if request:
            url = request.url
            data = request.text
        self.url = url
        self.data = data
        self.crawled = datetime.datetime.now()

    @property
    def links(self):
        soup = BeautifulSoup(self.data, 'html.parser')
        dem_links = [ a_tag.get('href') for a_tag in soup.find_all('a') ]
        for i, link in enumerate(dem_links):
            parsed_url = urlparse(link)
            if not parsed_url.netloc:
                dem_links[i] = urljoin(self.url, link)
                parsed_url = urlparse(dem_links[i])
            link_host = get_host(parsed_url.netloc)
            if link_host.has_page(parsed_url.path) or not want(parsed_url.path):
                dem_links[i] = None
        return [ link for link in dem_links if link ]

    @property
    def path(self):
        return urlparse(self.url).path
