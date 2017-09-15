import wx
import wx.grid
import wx.lib.scrolledpanel as scrolled
import wx.stc

import dbDataTable
import resultSet


class myGrid(wx.grid.Grid):
    """A customized WxWidget Grid with a dbDataTable as datasource"""

    def __init__(self, parent, resultSet: resultSet):
        wx.grid.Grid.__init__(self, parent)
        # Make the label font light
        self.SetLabelFont(wx.Font(wx.NORMAL_FONT.GetPointSize(),
                                  wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL,
                                  wx.FONTWEIGHT_LIGHT,
                                  False,
                                  wx.EmptyString))

        self.EnableDragRowSize(False)

        table = dbDataTable.DbDataTable(resultSet)
        self.SetTable(table, True)

        # resize label height to be consistent with the cells one
        self.SetColLabelSize(self.CellToRect(0, 0)[3])
        self.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # readOnly
        self.EnableEditing(False)

    def SetMinMaxSize(self, size: (int, int)):
        """Clamp the size of the grid to the desired value"""
        sbh = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        self.SetMaxClientSize((size[0] - sbh, size[1]))
        self.SetMinClientSize((size[0] - sbh, size[1]))


class scrolledGrid(scrolled.ScrolledPanel):
    """widget reprensenting many grid in one scrolled area"""

    def __init__(self, parent, resultSet):
        scrolled.ScrolledPanel.__init__(self, parent, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.grids = []

        for r in resultSet:
            g = myGrid(self, r)
            self.grids.append(g)

            s = parent.GetClientSize()
            g.SetMinMaxSize((s[0], 400))

            vbox.Add(g, 0, wx.ALL, 0)
            vbox.Add((20, 0))

        self.SetSizer(vbox)
        self.SetupScrolling(True, True)
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        s = self.GetClientSize()
        for g in self.grids:
            g.SetMinMaxSize((s[0], 400))


class queryResultGrid(wx.Panel):
    """A widget to present one or more resultset and the asosciated messages"""

    def __init__(self, parent, resultSet, message):
        wx.Panel.__init__(self, parent)

        # Sizer
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        # splitter
        self.splitter = wx.SplitterWindow(self)
        self.splitter.SetSashGravity(1.0)

        # Grid
        self.grid = self._createGridFromResultset(self.splitter, resultSet)

        # Editor
        self.editor = wx.TextCtrl(
            self.splitter,
            style=wx.TE_MULTILINE,
            value=message)

        self.splitter.SplitHorizontally(self.grid, self.editor, -80)
        self.mainSizer.Add(self.splitter, 1, wx.ALL | wx.EXPAND, 0)

        if len(message) == 0:
            self.splitter.Unsplit(self.editor)
        if resultSet is None:
            self.splitter.Unsplit(self.grid)

        self.SetSizer(self.mainSizer)
        self.Layout()

    def _createGridFromResultset(self, parent, resultSet):
        if resultSet is None:
            # there was an error, or no resultset at all
            # (insert, update or just print statment)
            # so we return a dummy control
            grid = wx.Panel(parent)
        elif len(resultSet) == 1:
            # Only one grid to display
            grid = myGrid(parent, resultSet[0])
        else:
            # Multi grid
            grid = scrolledGrid(parent, resultSet)
        return grid


if __name__ == '__main__':
    import sqlServer

    q = sqlServer.SqlServer(server="bt1shx0p",
                            instance="btsqlbcmtst2",
                            database="BCM",
                            IntegratedSecurity=True)
    r = q.Query("print 'begin';select top 100 * from op_operation;\
                 select top 25 * from dico_parametre;print 'hello';\
                 select top 10 * from dico_typenwobject;print 'World'")
    # r = q.Query("select top 100 * from op_operation;select top")
    # r = q.Query("print 'Hello World';")

    app = wx.App()

    frame = wx.Frame(None, -1, "Multi ResultSet grid view test",
                     wx.DefaultPosition, (640, 480))
    qr = queryResultGrid(frame, r, q.messages)
    frame.Show()
    app.MainLoop()

    r = q.Query("select top 100 * from op_operation")
    frame = wx.Frame(None, -1, "Single ResultSet grid view test",
                     wx.DefaultPosition, (640, 480))
    qr = queryResultGrid(frame, r, q.messages)
    frame.Show()
    app.MainLoop()

    r = q.Query("select * from op_op")
    frame = wx.Frame(None, -1, "Error test", wx.DefaultPosition, (640, 480))
    qr = queryResultGrid(frame, r, q.messages)
    frame.Show()
    app.MainLoop()

    r = q.Query("print 'Hello World';")
    frame = wx.Frame(None, -1, "Message only test",
                     wx.DefaultPosition, (640, 480))
    qr = queryResultGrid(frame, r, q.messages)
    frame.Show()
    app.MainLoop()
