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

    def get(self):
        return self.equeue.get()

    def getfd(self):
        return self.equeue._reader.fileno()

class EventClient(object):
    def __init__(self, events, i):
        self.events = events
        self.i = i

    def starting(self):
        self.events.put(StartingEvent(self.i))

    def retrieving(self):
        self.events.put(RetrievingEvent(self.i))

    def parsing(self):
        self.events.put(ParsingEvent(self.i))

    def downloading(self):
        self.events.put(DownloadingEvent(self.i))

    def extracting(self):
        self.events.put(ExtractingEvent(self.i))

    def done(self):
        self.events.put(DoneEvent(self.i))

    def processed(self):
        self.events.put(ProcessedEvent(self.i))

    def exception(self, e):
        self.events.put(ExceptionEvent(self.i, e))

class Event(object):
    def __init__(self, i):
        self.i = i

    def getText(self):
        raise NotImplementedError()

    def getEventType(self):
        raise NotImplementedError()

class EventType(Enum):
    status = 1
    processed = 2
    error = 3

class StatusEvent(Event):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return EventType.status

class StartingEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Starting"

class RetrievingEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Retrieving"

class ParsingEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Parsing"

class DownloadingEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Downloading"

class ExtractingEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Extracting"

class DoneEvent(StatusEvent):
    def __init__(self, i):
        super().__init__(i)

    def getText(self):
        return "Done"

class ProcessedEvent(Event):
    def __init__(self, i):
        super().__init__(i)

    def getEventType(self):
        return EventType.processed

class ExceptionEvent(Event):
    def __init__(self, i, e):
        super().__init__(i)
        self.e = e

    def getEventType(self):
        return EventType.error

