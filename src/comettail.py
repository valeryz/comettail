from twisted.internet import reactor, process, defer
from twisted.application import service
from twisted.web import server, resource
import os
import json
import uuid
from itertools import takewhile

BUFFER_SIZE = 1024
CHILD_KEEP_TIMEOUT = 10 # seconds
MAX_RESPONSE_SIZE = 1024

class TailProtocol(process.ProcessProtocol):

    """
    a process protocol that receives the data from the process and fires a
    given deferred
    """

    def __init__(self):
        self.deferred = defer.Deferred()
        self.buffer = ""
        self.timer = None
        self.chunks = []
        self.chunk_count = 0

    def _timeout(self):
        self.timer = None
        self.deferred.callback(self.buffer)
        self.buffer = ""
        self.deferred = Deferred()

    def childDataReceived(self, childFD, data):
        """
        send data from the child process down the deferred
        """
        if not data:
            return
        if childFD == 1:                # STDOUT
            self.buffer += data
            if len(self.buffer) > BUFFER_SIZE:
                if self.timer:
                    self.timer.cancel()
                self.deferred.callback((self, self.buffer)
                self.buffer = ""
                self.deferred = defer.Deferred()
            else:
                if not self.timer:
                    self.timer = reactor.callLater(0.2, self._timeout)

class FileMonitor:
    def __init__(self, filename):
        # run 'tail -f' subprocess
        self.protocol = TailProtocol()
        self.pool = []
        reactor.spawnProcess(self.protocol,
                             "tail", args=["tail", "-f", filename],
                             env=os.environ)

    def get_data(self, fromchunk, bufid):
        """
        get the latest lines of the 'tail -f' subprocess
        """
        d = defer.Deferred()
        self.pool.append(d)
        return d

class MonitorResource(resource.Resource):
    isLeaf = True
    def __init__(self, monitor):
        self.monitor = monitor

    def _reply(self, reply, request):
        request.write(str(reply))
        request.finish()

    def render_GET(self, request):
        d = self.monitor.get_data()
        d.addCallback(self._reply, request)
        return server.NOT_DONE_YET


class Buffer:

    def __init__(self, filename):
        """
        initialize buffer for a given filename and launch the 'tail -f'
        """
        self.filename = filename
        self.chunks = []
        self.chunk_count
        # spawnProcess
        self.bufid = uuid.uuid4().hex
        self.waiting_deferreds = []

    def _finish_getting(self, _, fromchunk):
        if not fromchunk:
            fromchunk = -1
        data = ""
        last_chunk = None
        for chunk_num, chunk_data in reversed(self.chunks):
            if chunk_num <= fromchunk:
                break
            last_chunk = chunk_num
            data += chunk_data
            if len(data) > MAX_RESPONSE_SIZE:
                break
        if data:
            return defer.succeed({
                'from' : last_chunk,
                'data' : data
                'bufid' : self.bufid,
                })
        else:
            d = defer.Deferred()
            d.addCallback(self._finish_getting, fromchunk)
            self.waiting_deferreds.append(d)
            return d

    def get_data(self, fromchunk, bufid):
        if bufid != self.bufid:
            fromchunk = None
        return self._finish_getting(None, fromchunk)

class FileBuffers:
    def __init__(self):
        self.buffers = {}
        self.timers = {}

    def _timeout(self, filename):
        """
        Delete a buffer that hasn't been used for long
        """
        del self.timers[filename]
        buf = buffers['filename']
        del self.buffers['filename']
        buf.shutdown()

    @defer.inlineCallbacks
    def get_data(self,  filename, fromchunk, bufid):
        try:
            buf = self.buffers[filename]
        except KeyError:
            buf = yield Buffer(filename)
            self.buffers[filename] = buf
            self.timers[filename](reactor.callLater(CHILD_KEEP_TIMEOUT,
                                                    self._timeout, filename))
        try:
            timer = self.timers[filename]
            timer.reset(CHILD_KEEP_TIMEOUT)
        except KeyError:
            pass
        return buf.get_data(fromchunk, bufid)

def format_result(result):
    return json.dumps(result)

class CometTailServer(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)
        self.filebuffers = FileBuffers()

    def render_GET(self, request):
        filename = request.args['filename']
        if not filename:
            return resource.ErrorPage(403, "No filename specified",
                                      "No filename specified")
        filename = filename[0]
        fromchunk = request.args['from']
        if fromchunk:
            fromchunk = fromchunk[0]
        bufid = request.args['bufid']
        if bufid:
            bufid = bufid[0]
        d = self.filebuffers.get_data(filename, fromchunk, bufid)
        def finish_result(result):
            request.write(format_result(result))
            request.finish()
        d.addCallback(finish_result)
        return server.NOT_DONE_YET

def comettail():
    # TODO: create monitors
    site = server.Site(CometTailServer())
    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    comettail()
