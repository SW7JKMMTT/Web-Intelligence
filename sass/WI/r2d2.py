from reppy.cache import RobotsCache

agent = 'spoderman'
sandcrawler = RobotsCache()

def is_allowed(url):
    try:
        return sandcrawler.allowed(url, agent)
    except:
        return False


