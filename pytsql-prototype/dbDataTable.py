import wx.grid

import resultSet


class DbDataTable(wx.grid.GridTableBase):

    def __init__(self, resultSet: resultSet):
        wx.grid.GridTableBase.__init__(self)

        self.resultSet = resultSet

        self.attr = wx.grid.GridCellAttr()
        self.attr.SetTextColour("black")

        self.nullAttr = wx.grid.GridCellAttr()
        self.nullAttr.SetTextColour("light grey")

    def GetAttr(self, row: int, col: int, kind):
        if self.resultSet.data[row][col] is None:
            self.nullAttr.IncRef()
            return self.nullAttr

        self.attr.IncRef()
        return self.attr

    # This is all it takes to make a custom data table to plug into a
    # wxGrid.  There are many more methods that can be overridden, but
    # the ones shown below are the required ones.  This table simply
    # provides strings containing the row and column values.

    def GetColLabelValue(self, col):
        return str(self.resultSet.description[col][0])

    def GetNumberRows(self):
        return len(self.resultSet.data)

    def GetNumberCols(self):
        return len(self.resultSet.description)

    def IsEmptyCell(self, row, col):
        return False

    def GetValue(self, row, col):

        data = self.resultSet.data[row][col]
        if data is None:
            return "null"

        if type(data) is bool:
            if data is True:
                return "1"
            else:
                return "0"

        data = str(data)
        # for performance reason, we clamp the size of strings
        return data[:1000]

    def SetValue(self, row, col, value):
        # we are readonly
        pass
