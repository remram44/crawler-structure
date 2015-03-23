import itertools
from twisted.internet import reactor


class Crawler(object):
    """A crawler.

    Currently doesn't do anything useful, just generate some events to test the
    tracking code.
    """
    def __init__(self, query):
        self._observers = set()
        self.query = query
        reactor.callLater(1, self._fake_result)

    def add_observer(self, obs):
        self._observers.add(obs)

    def remove_observer(self, obs):
        self._observers.discard(obs)

    def _notify_observers(self, func, *args, **kwargs):
        for obs in list(self._observers):
            if hasattr(obs, func):
                getattr(obs, func)(*args, **kwargs)

    def _fake_result(self, num=0):
        self._notify_observers('crawler_result', '%s %d' % (self.query, num))
        if num <= 10:
            reactor.callLater(1, self._fake_result, num + 1)
        else:
            self._notify_observers('crawler_done', self.query)


class CrawlerManager(object):
    """Global object holding all the crawlers.

    This is useful because HTTP is stateless, so tracking requests need to be
    able to find a crawler from an identifier.
    """
    def __init__(self):
        self._crawler_ids = itertools.count()
        self._crawlers = {}

    def new_crawler(self, query):
        """Creates a new crawler and returns its ID.
        """
        crawler_id = next(self._crawler_ids)
        self._crawlers[crawler_id] = Crawler(query)
        return crawler_id, None

    def get_crawler(self, crawler_id):
        """Gets a crawler by its ID.

        :raises KeyError: if the crawler doesn't exist.
        """
        return self._crawlers[crawler_id]
