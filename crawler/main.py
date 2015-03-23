from autobahn.twisted.resource import WebSocketResource
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File


class UpdateWSProtocol(WebSocketServerProtocol):
    _client_ids = 0

    def __init__(self):
        self._client_id = UpdateWSProtocol._client_ids
        UpdateWSProtocol._client_ids += 1
        self._socket_open = False

    def onOpen(self):
        print "client %d connected" % self._client_id
        self._socket_open = True
        reactor.callLater(1, self._send_data)

    def onMessage(self, payload, isBinary):
        print "got message from client %d" % self._client_id

    def _send_data(self, num=0):
        if self._socket_open:
            print "sending message to client %d" % self._client_id
            self.sendMessage("msg %d" % num, False)
            reactor.callLater(1, self._send_data, num + 1)

    def onClose(self, wasClean, code, reason):
        print "client %d disconnected (%s): %s" % (
            self._client_id,
            "clean" if wasClean else "not clean",
            reason)
        self._socket_open = False


root = Resource()
root.putChild("", File('index.html'))
updatews_factory = WebSocketServerFactory('ws://0.0.0.0:8080')
updatews_factory.protocol = UpdateWSProtocol
root.putChild("conn", WebSocketResource(updatews_factory))


def main():
    log.startLogging(sys.stderr)

    factory = Site(root)
    reactor.listenTCP(8080, factory)
    reactor.run()
