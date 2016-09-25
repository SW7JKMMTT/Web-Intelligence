from multiprocessing import Queue
from enum import Enum

class EventQueue(object):
    def __init__(self):
        self.equeue = Queue()
        self.i = 0

    def connect(self):
        i = self.i
        self.i += 1
        return EventClient(self.equeue, i)

    def hasEvents(self):
        return not self.equeue.empty()

    def size(self):
        return self.equeue.qsize()

    def get(self):
        return self.equeue.get()

    def getfd(self):
        return self.equeue._reader.fileno()

class EventClient(object):
    def __init__(self, events, i):
        self.events = events
        self.i = i

    def send(self, event):
        self.events.put(event)

class CrawlerEventClient(object):
    def __init__(self, ec):
        self.ec = ec
        self.i = self.ec.i
        self.state = 0

    def starting(self):
        if self.state != 1:
            self.state = 1
            self.ec.send(StartingEvent(self.i))

    def retrieving(self):
        if self.state != 2:
            self.state = 2
            self.ec.send(RetrievingEvent(self.i))

    def parsing(self):
        if self.state != 3:
            self.state = 3
            self.ec.send(ParsingEvent(self.i))

    def downloading(self):
        if self.state != 4:
            self.state = 4
            self.ec.send(DownloadingEvent(self.i))

    def extracting(self):
        if self.state != 5:
            self.state = 5
            self.ec.send(ExtractingEvent(self.i))

    def done(self):
        if self.state != 6:
            self.state = 6
            self.ec.send(DoneEvent(self.i))

    def processed(self):
        self.ec.send(ProcessedEvent(self.i))

    def exception(self):
        self.ec.send(ExceptionEvent(self.i))

class WriterEventClient(object):
    def __init__(self, ec):
        self.ec = ec
        self.i = self.ec.i

    def processing(self, url):
        self.ec.send(WriterProcessingEvent(self.i, url))

    def done(self):
        self.ec.send(WriterDoneEvent(self.i))

    def exception(self):
        self.ec.send(WriterExceptionEvent(self.i))

class Event(object):
    def __init__(self):
        pass

    def getEventType(self):
        raise NotImplementedError()

class CrawlerEventType(Enum):
    status = 1
    processed = 2
    error = 3

class CrawlerEvent(Event):
    def __init__(self, i):
        self.i = i

class CrawlerStatusEvent(CrawlerEvent):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return CrawlerEventType.status

    def getText(self):
        raise NotImplementedError()

class StartingEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Starting"

class RetrievingEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Retrieving"

class ParsingEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Parsing"

class DownloadingEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Downloading"

class ExtractingEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Extracting"

class DoneEvent(CrawlerStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Done"

class ProcessedEvent(CrawlerEvent):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return CrawlerEventType.processed

class ExceptionEvent(CrawlerEvent):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return CrawlerEventType.error

class WriterEventType(Enum):
    status = 1
    error = 3

class WriterEvent(Event):
    def __init__(self, i):
        self.i = i

class WriterStatusEvent(CrawlerEvent):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return WriterEventType.status

    def getText(self):
        raise NotImplementedError()

class WriterProcessingEvent(WriterStatusEvent):
    def __init__(self, i, url):
        super().__init__(i)
        self.url = url

    def getText(self):
        return self.url

class WriterDoneEvent(WriterStatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Done" 

class WriterExceptionEvent(WriterEvent):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return WriterEventType.error

