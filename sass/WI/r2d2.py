from reppy.cache import RobotsCache

agent = 'spoderman'
sandcrawler = RobotsCache(timeout=2)

def is_allowed(url):
    try:
        return sandcrawler.allowed(url, agent)
    except:
        return False

def crawl_delay(url):
    try:
        delay = sandcrawler.delay(url, agent)
        Print('Crawl delay for', url, delay)
        return delay if delay else 1
    except:
        return 1

