import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import threading
import wx
import sql
import ui

class RequestHandler(SimpleXMLRPCRequestHandler):
    # Restrict to a particular path.
    rpc_paths = ('/RPC2',)

class tdsKitService:
    def __init__(self, mainFrame):
        self.frame = mainFrame

    def connect(self, viewId, server, instance=None, database=None, user=None, password=None):
        wx.CallAfter(self.frame.new_connection, viewId, server=server, instance= instance, database = database, user = user, password = password)
        return "OK"

    def exec_query_async(self, viewid, query):
        wx.CallAfter(self.frame.execute_query_async,viewid,query)
        return "OK"

    def script_object(self, viewid, schema_name, object_name):
        srv = self.frame.views[viewid].srv
        script = srv.script_object(schema_name,object_name)
        return script

    def delete_view(self, viewid):
        wx.CallAfter(self.frame.delete_view,viewid)
        return "OK"

    def switch_to(self, viewid):
        wx.CallAfter(self.frame.switch_to,viewid)
        return "OK"

    def cancel(self, viewid):
        srv = self.frame.views[viewid].srv
        srv.cancel()
        return "OK"

    def sphelp_object(self, viewid, object_name):
        wx.CallAfter(self.frame.execute_query_async,viewid,"sp_help '"+object_name+"'")
        return "OK"

    def get_current_db(self, viewid):
        srv = self.frame.views[viewid].srv
        return srv.get_current_db()

    def ping(self):
        return True


class tdsKitServiceThread(threading.Thread):
    def __init__(self, frame):
        threading.Thread.__init__(self)
        self._frame = frame

    def run(self):
        tdsKitService_run(self._frame)

    def stop(self):
        tdsKitService_stop()

class MainFrame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, size=(640, 480))
        self.views = {}
        self.current_viewid = None

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.choicebook = wx.Listbook(self)
        self.vbox.Add(self.choicebook, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(self.vbox)

        # self.choicebook.GetChoiceCtrl().Show(False)
        # self.choicebook.GetListView().Show(False)
        self.Layout()
        self.Show(True)
        # self.res = ui.QueryEditor(self)
        
    def new_connection(self, viewid, server: str, instance: str=None, port: int = 1433,
                       database: str = "master", user: str = None, password: str = None):
        query = ui.QueryEditor(self.choicebook,False)
        query.xmlrpcclient = xmlrpcclient
        query.viewid = viewid
        conn = sql.ConnectionInfo(server,instance,port,database,user,password)
        query.connect(conn)

        self.delete_view(viewid)
        self.views[viewid] = query
        
        self.choicebook.AddPage(self.views[viewid],str(viewid))
        self.switch_to(viewid)

    def delete_view(self, viewid):
        if viewid in self.views:
            page = self.choicebook.FindPage(self.views[viewid])
            print("try delete"+str(page))
            if page != wx.NOT_FOUND:
                print("Delete")
                self.choicebook.DeletePage(page)
                self.views.pop(viewid,None)
                
                page = self.choicebook.GetSelection()
                if page != wx.NOT_FOUND:
                    self.current_viewid = self.choicebook.GetPageText(page)

    def cancel_query(self, viewid):
        if viewid in self.views:
            self.views[viewid].cancel()
        #self.switch_to(viewid)

    def execute_query_async(self, viewid, query):
        if viewid in self.views:
            self.views[viewid].execute_async(query)
            self.switch_to(viewid)

    def switch_to(self, viewid):
        if viewid in self.views:
            page = self.choicebook.FindPage(self.views[viewid])
            self.choicebook.ChangeSelection(page)
            self.current_viewid = viewid

        
def tdsKitService_run(frame):
    xmlrpcserver.register_introspection_functions()

    xmlrpcserver.register_instance(tdsKitService(frame))

    # Run the server's main loop
    xmlrpcserver.serve_forever()


def tdsKitService_stop():
    xmlrpcserver.shutdown()

xmlrpcserver = SimpleXMLRPCServer(("localhost", 8000),
                            requestHandler=RequestHandler, allow_none=True)

xmlrpcclient = xmlrpc.client.ServerProxy('http://127.0.0.1:8001', allow_none=True)

app = wx.App()
frame = MainFrame(title="TdsKit")

k = tdsKitServiceThread(frame)
k.start()

app.MainLoop()

k.stop()