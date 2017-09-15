import wx
import queryResultGrid


class Page(queryResultGrid.queryResultGrid):
    def __init__(self, parent, title, id, sqlServer):
        super().__init__(parent, None, "")
        self.connection = sqlServer
        self.id = id
        self.title = title


class MainFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(640, 480))

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.noteBook = wx.Notebook(self)

        self.grids = {}

        self.vbox.Add(self.noteBook, 1, wx.ALL | wx.EXPAND, 0)

        self.statusBar = self.CreateStatusBar()

        self.SetSizer(self.vbox)
        self.Layout()

        self.Show(True)

    def newPage(self, title, id, sqlServer):
        self.grids[id] = Page(self.noteBook, title, id, sqlServer)
        self.noteBook.AddPage(self.grids[id], title, True)


if __name__ == '__main__':

    import sqlServer

    app = wx.App()

    frame = MainFrame(None, "TdsKit")
    q = sqlServer.SqlServer(
        server="bt1shx0p",
        instance="btsqlbcmtst2",
        database="BCM",
        IntegratedSecurity=True)
    frame.newPage("plop", 1, q)
    frame.newPage("toto", 2, q)

    app.MainLoop()
