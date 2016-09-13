import hashlib


class CrawlQueue:
    __domains = []
    __visited_domains = []

    def __init__(self):
        t = 1

    def add_url(self, url):
        hasher = hashlib.new("md5")

        hasher.update(url)

        hasher.hexdigest()

        self.__domains