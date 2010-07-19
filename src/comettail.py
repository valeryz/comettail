# Twisted server for 'tail -F' COMET streams

from twisted.internet import reactor, process, defer, error, protocol
from twisted.internet import interfaces
from twisted.application import service
from twisted.web import server, resource, static
import os
import json
import uuid

BUFFER_SIZE = 1024
CHILD_KEEP_TIMEOUT = 20 # seconds
MAX_RESPONSE_SIZE = 1024

class TailProtocol(protocol.ProcessProtocol):

    """
    a process protocol that receives the data from the process and fires a
    given deferred
    """

    def __init__(self, buf):
        self.buf = buf

    def childDataReceived(self, childFD, data):
        """
        send data from the child process down the deferred
        """
        if not data:
            return
        if childFD == 1:
            # TODO: smooth it out!, don't return small chunks often,
            # combine them!
            self.buf.chunk_arrived(data)


class Buffer(object):

    def __init__(self, filename, container):
        """
        initialize buffer for a given filename and launch the 'tail -F'
        """
        self.filename = filename
        self.container = container
        self.chunks = []
        self.chunk_count = 0
        self.bufid = uuid.uuid4().hex
        self.waiting_deferreds = []
        # spawnProcess
        proto = TailProtocol(self)
        self.process = reactor.spawnProcess(proto, "tail",
                                            args=["tail", "-F", filename],
                                            env=os.environ)
        self.timer = None

    def _schedule_timer(self):
        if self.timer:
            self.timer.reset(CHILD_KEEP_TIMEOUT)
        else:
            self.timer = reactor.callLater(CHILD_KEEP_TIMEOUT, self._timeout)

    def _finish_getting(self, _, fromchunk, finish_deferred):
        if not fromchunk:
            fromchunk = -1
        data = ""
        last_chunk = None
        for chunk_num, chunk_data in reversed(self.chunks):
            if chunk_num <= fromchunk:
                break
            last_chunk = chunk_num
            data = chunk_data + data
            if len(data) > MAX_RESPONSE_SIZE:
                break
        if data:
            return defer.succeed({
                'from' : last_chunk,
                'data' : data,
                'bufid' : self.bufid,
                })
        else:
            d = defer.Deferred()
            d.addCallback(self._finish_getting, fromchunk, None)
            self.waiting_deferreds.append(d)
            if finish_deferred:
                def remove_d(_):
                    try:
                        self.waiting_deferreds.remove(d)
                    except ValueError:
                        pass
                    if not self.waiting_deferreds:
                        self._schedule_timer()
                finish_deferred.addBoth(remove_d)
            return d

    def get_data(self, fromchunk, bufid, finish_deferred):
        if bufid != self.bufid:
            fromchunk = None
        if self.timer:
            self.timer.cancel()
            self.timer = None
        return self._finish_getting(None, fromchunk, finish_deferred)

    def chunk_arrived(self, data):
        """
        handle arrival of a new chunk data from the 'tail -F' process
        """
        self.chunk_count += 1
        self.chunks.append((self.chunk_count, data))
        deferreds = self.waiting_deferreds
        self.waiting_deferreds = []
        for d in deferreds:
            d.callback(None)
        self._schedule_timer()

    def _timeout(self):
        """
        shut down the 'tail' -F process and discard all data
        """
        try:
            self.process.signalProcess("TERM")
        except error.ProcessExitedAlready:
            pass
        self.container.remove(self.filename)


class FileBuffers(object):
    def __init__(self):
        self.buffers = {}

    def get_data(self,  filename, fromchunk, bufid, finish_deferred):
        try:
            buf = self.buffers[filename]
        except KeyError:
            buf = Buffer(filename, self)
            self.buffers[filename] = buf
        return buf.get_data(fromchunk, bufid, finish_deferred)

    def remove(self, filename):
        try:
            del self.buffers[filename]
        except KeyError:
            pass

def format_result(result):
    return json.dumps(result)

class CometTailServer(resource.Resource):

    isLeaf = True

    def __init__(self):
        resource.Resource.__init__(self)
        self.filebuffers = FileBuffers()

    def render_GET(self, request):
        filename = request.args.get('filename')
        if not filename:
            return resource.ErrorPage(403, "No filename specified",
                                      "No filename specified")
        filename = filename[0]
        fromchunk = request.args.get('from')
        if fromchunk:
            try:
                fromchunk = int(fromchunk[0])
            except (TypeError, ValueError):
                fromchunk = None
        bufid = request.args.get('bufid')
        if bufid:
            bufid = bufid[0]
        d = defer.maybeDeferred(self.filebuffers.get_data,
                                filename, fromchunk, bufid,
                                request.notifyFinish())
        def finish_result(result):
            print result
            request.write(format_result(result))
            request.finish()
        d.addCallback(finish_result)
        return server.NOT_DONE_YET

def comettail():
    thisdir = os.path.dirname(__file__)
    root = resource.Resource()
    root.putChild('dashboard', static.File(os.path.join(thisdir, 'dashboard')))
    root.putChild('css', static.File(os.path.join(thisdir, 'css')))
    root.putChild('js', static.File(os.path.join(thisdir, 'js'),
                                    defaultType="application/x-javascript"))
    root.putChild('comettail', CometTailServer())
    site = server.Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()


if __name__ == '__main__':
    comettail()
