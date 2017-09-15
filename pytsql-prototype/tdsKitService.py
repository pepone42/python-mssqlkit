from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import sqlServer
import wx
import threading


class RequestHandler(SimpleXMLRPCRequestHandler):
    # Restrict to a particular path.
    rpc_paths = ('/RPC2',)


class tdsKitService:
    def __init__(self, mainFrame):
        self.connections = {}
        self.frame = mainFrame

    def Connect(self, connectionId, server, instance, database):
        conn = sqlServer.SqlServer(server=server,
                                   instance=instance,
                                   database=database,
                                   IntegratedSecurity=True)
        self.connections[connectionId] = conn
        return "Ok"

    def _threadedExecQuery(self, connectionId, sqlQuery):
        r = self.connections[connectionId].Query(sqlQuery)
        m = self.connections[connectionId].messages
        # self.frame.sendNewResultSetEvent(r)
        wx.CallAfter(self.frame.newResultSet, r, m)

    def ExecQuery(self, connectionId, sqlQuery):
        # wx.CallAfter(self.frame.startExecutingQuery)
        threading.Thread(
            target=self._threadedExecQuery,
            args=(connectionId, sqlQuery)).start()
        return "OK"

    def Disconnect(self, connectionId):
        self.connections[connectionId].Close()
        return "Ok"

    def GetCurentDatabase(self, connectionId) -> str:
        return self.connections[connectionId].GetCurrentDatabase()


server = SimpleXMLRPCServer(("localhost", 8000),
                            requestHandler=RequestHandler)


def run(frame):
    server.register_introspection_functions()

    server.register_instance(tdsKitService(frame))

    # Run the server's main loop
    server.serve_forever()


def stop():
    server.shutdown()


if __name__ == '__main__':
    run(None)
    # coté client : s = xmlrpc.client.ServerProxy('http://127.0.0.1:8000',
    #                                              allow_none=True)
    #               s.Connect(1,"bt1shx0p","btsqlbcmtst2","BCM")
    #               s.GetCurentDatabase(1)
    #               s.Disconnect(1)
