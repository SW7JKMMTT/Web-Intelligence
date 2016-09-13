class Domain:
    def __init__(self, url):
        self.url = url
        self.refs = 0

    def add_ref(self):
        self.refs += 1
