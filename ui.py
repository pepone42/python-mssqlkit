"""Gui module"""

import wx
import wx.grid
import wx.lib.scrolledpanel as scrolled

class DataGrid(wx.grid.Grid):
    """A customized WxWidget Grid with a dbDataTable as datasource"""

    def __init__(self, parent, data_table):
        wx.grid.Grid.__init__(self, parent)
        # Make the label font light
        self.SetLabelFont(wx.Font(wx.NORMAL_FONT.GetPointSize(),
                                  wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL,
                                  wx.FONTWEIGHT_LIGHT,
                                  False,
                                  wx.EmptyString))

        self.EnableDragRowSize(False)

        table = data_table
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


class _multiScrolledGrid(scrolled.ScrolledPanel):
    """widget reprensenting many grid in one scrolled area"""

    def __init__(self, parent, dataTables):
        scrolled.ScrolledPanel.__init__(self, parent, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.grids = []

        for r in dataTables:
            g = dataGrid.DataGrid(self, r)
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


class MultiGrid(wx.Panel):
    """A widget to present one or more grid"""

    def __init__(self, parent, dataTables):
        wx.Panel.__init__(self, parent)

        # Sizer
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # Grid
        self.grids = self._createGridFromResultset(self, dataTables)

        mainSizer.Add(self.grids, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(mainSizer)
        self.Layout()

    def _createGridFromResultset(self, parent, dataTables):
        if dataTables is None:
            # No Data?
            # we return a dummy control then
            grid = wx.Panel(parent)
        elif len(dataTables) == 1:
            # Only one grid to display
            grid = dataGrid(parent, dataTables[0])
        else:
            # Multi grid
            grid = _multiScrolledGrid(parent, dataTables)
        return grid
