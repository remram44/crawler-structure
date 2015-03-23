from autobahn.twisted.resource import WebSocketResource
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import itertools
from jinja2 import PackageLoader, Environment
import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.util import redirectTo

from crawler.crawl import CrawlerManager


crawler_manager = CrawlerManager()


class TemplatedResource(Resource):
    """A resource that renders a Jinja2 template on GET.
    """
    _environment = Environment(
        loader=PackageLoader('crawler', 'templates'))

    def __init__(self, template, **kwargs):
        Resource.__init__(self)
        self._template = self._environment.get_template(template)
        self._tpl_kwargs = kwargs

    def render_GET(self, request):
        return self._template.render(**self._tpl_kwargs).encode('utf-8')


class CrawlResource(TemplatedResource):
    """Crawl page, starts a crawler and serves the page that will show status.
    """
    def __init__(self):
        TemplatedResource.__init__(self, 'crawl.html')

    def render_GET(self, request):
        return redirectTo('/', request)

    def render_POST(self, request):
        try:
            query = request.args['query'][0]
        except KeyError:
            return self._environment.get_template('error.html',
                                                  msg="Missing query")
        # Create a crawler
        crawler_id, msg = crawler_manager.new_crawler(query)
        return self._template.render(
            crawler_id=crawler_id, msg=msg,
            connect_addr='127.0.0.1:8080').encode('utf-8')


class TrackCrawlerWSProtocol(WebSocketServerProtocol):
    """Track a crawler via a WebSocket connection.
    """
    _client_ids = itertools.count()

    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self._client_id = next(self._client_ids)
        self._socket_open = False
        self._crawler = None

    def onOpen(self):
        print "client %d connected" % self._client_id
        self._socket_open = True

    def onClose(self, wasClean, code, reason):
        print "client %d disconnected (%s): %s" % (
            self._client_id,
            "clean" if wasClean else "not clean",
            reason)
        self._socket_open = False
        if self._crawler is not None:
            self._crawler.remove_observer(self)

    def onMessage(self, payload, isBinary):
        if self._crawler is not None:
            return
        try:
            crawler_id = int(payload)
            self._crawler = crawler_manager.get_crawler(crawler_id)
        except (ValueError, KeyError):
            self.sendMessage("Invalid crawler ID")
            self.sendClose()
            print "got invalid message from client %d" % self._client_id
        else:
            print "client %d now tracking crawler %d" % (self._client_id,
                                                         crawler_id)
            self._crawler.add_observer(self)

    def crawler_result(self, result):
        self.sendMessage(result)

    def crawler_done(self, query):
        self.sendMessage("done (%s)" % query)
        self._crawler.remove_observer(self)
        self.sendClose()


root = Resource()

# / ask for a query, POSTs to /crawl
root.putChild("", TemplatedResource('index.html'))

# /crawl gets the query, creates a crawler, serves the page on which the user
# will follow the crawling progress
# That page has the ID of the crawler, so that it can open a WebSocket
# connection (to /track.ws) and get updates for that crawler
root.putChild('crawl', CrawlResource())

# /track.ws is called by the Javascript on page /crawl
# It gets the ID of the crawler to track, and sends back the progress to be
# displayed to the client
trackws_factory = WebSocketServerFactory('ws://0.0.0.0:8080')
trackws_factory.protocol = TrackCrawlerWSProtocol
root.putChild('track.ws', WebSocketResource(trackws_factory))


def main():
    log.startLogging(sys.stderr)

    factory = Site(root)
    reactor.listenTCP(8080, factory)
    reactor.run()
