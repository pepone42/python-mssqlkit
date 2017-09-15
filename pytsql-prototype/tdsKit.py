import wx
import queryResultGrid
import tdsKitService
import threading


class tdsKitServiceThread(threading.Thread):
    def __init__(self, frame):
        threading.Thread.__init__(self)
        self._frame = frame

    def run(self):
        tdsKitService.run(self._frame)

    def stop(self):
        tdsKitService.stop()


class TdsKit(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(640, 480))

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.result = queryResultGrid.queryResultGrid(self, None, "Hello!")
        self.vbox.Add(self.result, 1, wx.ALL | wx.EXPAND, 0)
        self.SetSizer(self.vbox)
        self.Layout()

        self.statusBar = self.CreateStatusBar()

        self.Show(True)

    def startExecutingQuery(self):
        self.newResultSet(self, None, "Executing...")

    def newResultSet(self, newResultSet, newMessage):
        old = self.result
        self.result = queryResultGrid.queryResultGrid(
            self, newResultSet, newMessage)
        self.vbox.Replace(old, self.result)
        old.Destroy()
        self.Layout()


app = wx.App()

frame = TdsKit(None, "TdsKit")

k = tdsKitServiceThread(frame)
k.start()

app.MainLoop()

k.stop()
