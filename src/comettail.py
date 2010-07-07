from twisted.internet import reactor
from twisted.application import service
from twisted.web import server, resource

class FileMonitor:
    def __init__(self, filename):
        # run 'tail -f' subprocess

    def get_latest_lines(self):
        """

        """

class MonitorResource(resource.Resource):
    isLeaf = True
    def __init__(self, monitor):
        self.monitor = monitor

    def _reply(self, reply, request):
        request.write(str(reply))
        request.finish()

    def render_GET(self, request):
        # arrange for the stuff to return from monitor
        d = self.monitor.get_latest_lines()
        d.addCallback(self._reply, request)
        return server.NOT_DONE_YET

class CometTailServer(resource.Resource):
    def __init__(self, monitors):
        resource.Resource.__init__(self)
        for m in monitors:
            self.putChild(monitor.screen_filename, monitor)

def comettail():
    # TODO: create monitors
    site = server.Site(CometTailServer(monitors))
    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    comettail()
