from base64 import b64encode
import itertools
import urllib
from xml.etree import ElementTree
from twisted.internet import reactor
from twisted.python import log
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

from crawler import config


class Observable(object):
    def __init__(self):
        self.__observers = set()

    def add_observer(self, obs):
        self.__observers.add(obs)

    def remove_observer(self, obs):
        self.__observers.discard(obs)

    def _notify_observers(self, func, *args, **kwargs):
        for obs in list(self.__observers):
            if hasattr(obs, func):
                getattr(obs, func)(*args, **kwargs)


class Crawler(Observable):
    """A crawler.

    Currently doesn't do anything useful, just generate some events to test the
    tracking code.
    """
    agent = Agent(reactor)

    BING_URL = ('https://api.datamarket.azure.com'
                '/Bing/SearchWeb/v1/Web'
                '?Query=\'{query}\'')

    def __init__(self, query):
        Observable.__init__(self)

        self.query = query
        self._search_bing(query)

    def _search_bing(self, query):
        # Microsoft's doc is a joke
        # see http://stackoverflow.com/a/10844666/711380
        log.msg("searching bing for %s" % urllib.quote_plus(query))
        d = self.agent.request(
            'GET',
            self.BING_URL.format(query=urllib.quote_plus(query)),
            Headers({'User-Agent': ['twisted-crawler'],
                     'Authorization': [
                         'Basic %s' % b64encode('{key}:{key}'.format(
                             key=config.BING_KEY))]}),
            None)
        d.addCallback(self._bing_request)
        d.addErrback(self._error, "Bing request failed")

    def _bing_request(self, response):
        log.msg("request processed, reading response")
        d = readBody(response)
        d.addCallback(self._bing_response, response)

    def _bing_response(self, body, response):
        log.msg("got response")
        import pdb; pdb.set_trace()
        e = ElementTree.XML(body)
        #self._notify_observers('crawler_result', ...)
        #self._notify_observers('crawler_done', ...)

    def _error(self, err, msg):
        self._notify_observers('crawler_error', msg, err)
        return err


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
