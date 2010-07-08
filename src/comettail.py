from twisted.internet import reactor
from twisted.application import service
from twisted.web import server, resource

class TailProtocol(process.ProcessProtocol):

    """
    a process protocol that receives the data from the process and fires a
    given deferred
    """

    def __init__(self, deferred):
        self.deferred = deferred

    def childDataReceived(self, childFD, data):

class FileMonitor:
    def __init__(self, filename):
        # run 'tail -f' subprocess
        reactor.spawnProcess(

    def get_latest_lines(self):
        """
        get the latest lines of the 'tail -f' subprocess
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
