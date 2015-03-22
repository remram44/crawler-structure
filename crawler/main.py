import sys
from twisted.internet import reactor
from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET


class IndexPage(Resource):
    isLeaf = True

    def _handle_err(self, e, kill_list):
        print "canceled: %r" % (e,)
        for c in kill_list:
            c.cancel()

    def render_GET(self, request):
        print "render_GET"
        fin = request.notifyFinish()
        request.write('<!DOCTYPE html>\n'
                      '<html>\n'
                      '  <body>\n'
                      '    <h1>Loading:</h1>\n')
        kill_list = []
        call = reactor.callLater(1, self._render, request, kill_list)
        kill_list.append(call)
        fin.addErrback(self._handle_err, kill_list)
        return NOT_DONE_YET

    def _render(self, request, kill_list, num=0):
        print "_render"
        request.write('      <p>%d</p>\n' % num)
        if num < 10:
            call = reactor.callLater(1, self._render, request, kill_list, num + 1)
            kill_list[0] = call
        else:
            request.write('  </body>\n'
                          '</html>\n')
            request.finish()
            print "finish()"


index = IndexPage()


def main():
    log.startLogging(sys.stderr)

    factory = Site(index)
    reactor.listenTCP(8080, factory)
    reactor.run()
