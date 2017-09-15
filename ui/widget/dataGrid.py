import wx
import wx.grid


class DataGrid(wx.grid.Grid):
    """A customized WxWidget Grid with a dbDataTable as datasource"""

    def __init__(self, parent, dataTable):
        wx.grid.Grid.__init__(self, parent)
        # Make the label font light
        self.SetLabelFont(wx.Font(wx.NORMAL_FONT.GetPointSize(),
                                  wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL,
                                  wx.FONTWEIGHT_LIGHT,
                                  False,
                                  wx.EmptyString))

        self.EnableDragRowSize(False)

        table = dataTable
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
