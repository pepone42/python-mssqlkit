"""Gui module"""

import wx
import wx.grid
import wx.lib.scrolledpanel as scrolled
import wx.stc
import threading
import platform

import sql

"""
Datagrid: the base grid class
MultiscrolledGrid: A control that contain multiple grid
MultiGrid: Contain one Datagrid or one MultiscrolledGrid
ResultSetGrid: A control that contain MultiGrid and/or a Text aera

"""


class DbDataTable(wx.grid.GridTableBase):

    def __init__(self, resultSet):
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
        #return str(self.resultSet.description[col][0]+'\n'+self.resultSet.description[col][7])
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

    # def SetValue(self, row, col, value):
    #     # we are readonly
    #     pass


class DataGrid(wx.grid.Grid):
    """A customized WxWidget Grid with a dbDataTable as datasource"""

    def __init__(self, parent, data_table):
        wx.grid.Grid.__init__(self, parent)
        # Make the label font light
        self.SetLabelFont(wx.Font(wx.NORMAL_FONT.GetPointSize(),
                                  wx.FONTFAMILY_DEFAULT,
                                  wx.FONTSTYLE_NORMAL,
                                  wx.FONTWEIGHT_NORMAL,
                                  False,
                                  wx.EmptyString))

        self.SetCellHighlightPenWidth(1)

        self.EnableDragRowSize(False)
        self.table = DbDataTable(data_table)
        self.SetTable(self.table, True)

        # resize label height to be consistent with the cells one
        self.SetColLabelSize(self.CellToRect(0, 0)[3])
        self.SetColLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        # readOnly
        self.EnableEditing(False)
        self.EnableCellEditControl(False)

        if self.table.RowsCount>0:
            self.resize_columns_to_ideal_size(0, 100)

        # Event handling
        self.Bind(wx.PyEventBinder(wx.grid.wxEVT_GRID_COL_AUTO_SIZE),
                  self.col_auto_size_event)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.grid_select_cell_event, self)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.show_popup_menu)

        self.popup_copy_id = wx.NewId()
        self.popup_copy_with_header_id = wx.NewId()
        self.popup_copy_header_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.menu_event)

        if platform.system() == "Linux":
            self.hidden_panel = wx.Panel(parent,pos = self.GetPosition(), size = self.GetSize())
            self.hidden_panel.Show()
            self.hidden_panel.Bind(wx.EVT_MOUSE_EVENTS,self.mousewheel_event)
            print("Linux!")
            # for child in self.GetChildren():
            #     print(child.GetName()+" "+str(child))
            #     child.Bind(wx.EVT_MOUSE_EVENTS,self.mousewheel_event)

    def menu_event(self, e):
        print("Menu event "+str(e.GetId() ))
        
        i = e.GetId()
        if i == self.popup_copy_id:
            print(str(self.popup_copy_id))
            self.copy_selection_to_clipboard()
        elif i == self.popup_copy_with_header_id:
            self.copy_selection_to_clipboard(True)
        elif i == self.popup_copy_header_id:
            self.copy_selected_headers_to_clipboard()

    def show_popup_menu(self, event):
        menu = wx.Menu()
        menu.Append(self.popup_copy_id, "Copy\tCtrl+c")
        menu.Append(self.popup_copy_with_header_id, "Copy with headers\tCtrl-Shift-c")
        menu.Append(self.popup_copy_header_id, "Copy headers")

        self.PopupMenu(menu)
        menu.Destroy()


    def mousewheel_event(self, e):
        print("Mousewheel!")
        e.Skip()

    def grid_select_cell_event(self, evt):
        row = evt.GetRow()
        col = evt.GetCol()
        self.SelectBlock(row, col, row, col)
        evt.Skip()

    def get_display_value(self, row, col):
        d = self.table.resultSet.data[row][col]
        if d is None:
            return "NULL"
        elif type(d) is bool:
            if d is True:
                return "1"
            else:
                return "0"
        else:
            return str(d)

    def copy_selected_headers_to_clipboard(self):
        data = ""
        data = "\t".join(map(lambda col:
                             str(self.table.resultSet.description[col][0]), self.get_cols_with_selected_cells()))
        data = data+"\n"
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(data))
            wx.TheClipboard.Close()

    def copy_selection_to_clipboard(self, with_header: bool = False):
        data = ""
        if with_header:
            data = "\t".join(map(lambda col:
                                 str(self.table.resultSet.description[col][0]), self.get_cols_with_selected_cells()))
            data = data+"\n"

        for row in self.get_rows_with_selected_cells():
            data = data+"\t".join(
                map(lambda col:
                    self.get_display_value(row, col),
                    self.get_cols_with_selected_cells()))
            data += '\n'

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(data))
            wx.TheClipboard.Close()

    def on_key_down(self, e):

        if e.GetUnicodeKey() == ord('C') and e.CmdDown():
            if e.ShiftDown():
                self.copy_selection_to_clipboard(True)
            else:
                self.copy_selection_to_clipboard()
            e.Skip()
            return

        # propagate the event
        e.ResumePropagation(1)
        e.Skip()

    def get_rows_with_selected_cells(self):
        # if a column is selected -> return all the rows
        if len(self.GetSelectedCols()) > 0:
            print("Here")
            return list(range(0, self.table.GetNumberRows()))

        srows = self.GetSelectedRows()
        for i in self.GetSelectedCells():
            srows.append(i[0])

        top = self.GetSelectionBlockTopLeft()
        bottom = self.GetSelectionBlockBottomRight()
        for i in range(0, len(top)):
            srows = srows + list(range(top[i][0], bottom[i][0]+1))

        return sorted(list(set(srows)))

    def get_cols_with_selected_cells(self):
        # if a row is selected -> return all the columns
        if len(self.GetSelectedRows()) > 0:
            return list(range(0, self.table.GetNumberCols()))

        scols = self.GetSelectedCols()
        for i in self.GetSelectedCells():
            scols.append(i[1])

        top = self.GetSelectionBlockTopLeft()
        bottom = self.GetSelectionBlockBottomRight()
        for i in range(0, len(top)):
            scols = scols + list(range(top[i][1], bottom[i][1]+1))

        return sorted(list(set(scols)))

    def SetMinMaxSize(self, size: (int, int)):
        """Clamp the size of the grid to the desired value"""
        # TODO: if the resultset have less than 400px we don't want 
        # the space need for the vertcal scrollbar
        sbh = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        self.SetMaxClientSize((size[0] - sbh, size[1]))
        self.SetMinClientSize((size[0] - sbh, size[1]))

    def get_visible_cells(self):
        """Get the cells bbox visible in the viewport"""
        ux, uy = self.GetScrollPixelsPerUnit()
        sx, sy = self.GetViewStart()
        w, h = self.GetGridWindow().GetClientSize().Get()
        sx *= ux
        sy *= uy
        start_col = self.XToCol(sx)
        start_row = self.YToRow(sy)
        end_col = self.XToCol(sx + w, True)
        end_row = self.YToRow(sy + h, True)
        return start_row, end_row, start_col, end_col

    def get_visible_rows(self):
        """ get the start and end of the visible rows """
        start, end, _, _ = self.get_visible_cells()
        return start, end

    def get_label_best_size(self, col):
        data = str(self.table.resultSet.description[col][0])
        data = data[:1000]
        font = self.GetLabelFont()
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        width, height = dc.GetTextExtent(data)
        return width+12

    def get_cell_best_size(self, row, col):
        data = str(self.table.resultSet.data[row][col])
        data = data[:1000]
        font = self.GetCellFont(row, col)
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        width, height = dc.GetTextExtent(data)
        return width+12

    def resize_column_to_ideal_size(self, col, start_row=None, end_row=None):
        if start_row is None:
            start_row, end_row = self.get_visible_rows()
        start_row = min(start_row, self.table.GetNumberRows()-1)
        end_row = min(end_row, self.table.GetNumberRows()-1)

        max_size = max(self.GetColMinimalAcceptableWidth() +
                       1, self.get_label_best_size(col))
        for row in range(start_row, end_row+1):
            s = self.get_cell_best_size(row, col)
            if s > max_size:
                max_size = s
        self.SetColSize(col, max_size)

    def resize_columns_to_ideal_size(self, start_row=None, end_row=None):
        for col in range(0, self.table.GetNumberCols()):
            self.resize_column_to_ideal_size(col, start_row, end_row)

    def col_auto_size_event(self, e):
        print("col_auto_size_event")
        self.resize_column_to_ideal_size(e.GetRowOrCol())


class _multiScrolledGrid(scrolled.ScrolledPanel):
    """widget reprensenting many grid in one scrolled area"""

    def __init__(self, parent, dataTables):
        scrolled.ScrolledPanel.__init__(self, parent, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.grids = []

        for r in dataTables:
            g = DataGrid(self, r)
            self.grids.append(g)

            s = parent.GetClientSize()
            g.SetMinMaxSize((s[0], 400))

            vbox.Add(g, 0, wx.ALL, 0)
            vbox.Add((20, 0))

        self.SetSizer(vbox)
        self.SetupScrolling(True, True)
        self.Layout()
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event):
        s = self.GetClientSize()
        for g in self.grids:
            g.SetMinMaxSize((s[0], 400))


class MultiGrid(wx.Panel):
    """A widget to present one or more grid"""

    def __init__(self, parent, dataTables):
        wx.Panel.__init__(self, parent)

        # Sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Grid
        self.grids = _create_grid_from_resultset(self, dataTables)

        main_sizer.Add(self.grids, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(main_sizer)
        self.Layout()


def _create_grid_from_resultset(parent, data_tables):
    if len(data_tables) == 0: # is None:
        # No Data?
        # we return a dummy control then
        grid = wx.Panel(parent)
    elif len(data_tables) == 1:
        # Only one grid to display
        grid = DataGrid(parent, data_tables[0])
    else:
        # Multi grid
        grid = _multiScrolledGrid(parent, data_tables)
    return grid


class ResultSetGrid(wx.Panel):
    """ Mutli grid and/or a text message """

    def __init__(self, parent, datatables, message):
        wx.Panel.__init__(self, parent)
        # Sizer

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.note_book = wx.Notebook(self)
        self.vbox.Add(self.note_book, 1, wx.ALL | wx.EXPAND, 0)

        if datatables is not None and len(datatables) > 0: # there is Data to display
            self.grid = MultiGrid(self.note_book, datatables)
            self.note_book.AddPage(self.grid, "Result", True)
        if message is not None: # there is message to display
            self.message = wx.TextCtrl(
                self.note_book, value=message, style=wx.TE_MULTILINE | wx.TE_READONLY)
            self.note_book.AddPage(self.message, "Message", False)

        self.infoBar = wx.InfoBar(self)
        self.infoBar.SetShowHideEffects(
            wx.SHOW_EFFECT_NONE, wx.SHOW_EFFECT_NONE)
        self.vbox.Add(self.infoBar, wx.SizerFlags().Expand())

        self.SetSizer(self.vbox)
        self.Layout()

        self.Show(True)


class QueryEditor(wx.Panel):
    """ Sql editor with query result """

    def __init__(self, parent, with_editor: bool=True):
        self.srv = None
        self.is_running = False
        # self.metadata_cache = sql.MetadataCache()

        wx.Frame.__init__(self, parent)
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # editor
        #self.texteditor = wx.stc.StyledTextCtrl(self.splitter)
        self.with_editor = with_editor
        if self.with_editor == True:
            # splitter
            self.splitter = wx.SplitterWindow(self)
            self.splitter.SetSashGravity(1.0)

            self.texteditor = wx.TextCtrl(self.splitter, style=wx.TE_MULTILINE|wx.TE_RICH2)
            # TODO: sql styling
            self.texteditor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

            # Resultset
            self.result = ResultSetGrid(self.splitter, None, None)

            self.splitter.SplitHorizontally(self.texteditor, self.result, -150)
            self.splitter.Unsplit()
            self.vbox.Add(self.splitter, 1, wx.ALL | wx.EXPAND, 0)
        else:
            self.result = ResultSetGrid(self, None, None)
            self.vbox.Add(self.result, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(self.vbox)
        self.Layout()

        self.Show(True)

    def set_result(self, datatables, message):
        self.is_running = False
        if self.with_editor == True:
            new = ResultSetGrid(self.splitter, datatables, message)
            if self.splitter.IsSplit():
                # allready splitted, we swap the old result with the new one
                old = self.result
                print(str(old)+","+str(new))
                self.splitter.ReplaceWindow(old, new)
                self.result = new
                old.Destroy()
            else:
                # not splited -> only the editor is displayed -> with split and add the result control
            
                self.splitter.SplitHorizontally(self.texteditor, new, -150)
                self.result = new
        else:
            # no editor mode
            new = ResultSetGrid(self, datatables, message)
            old = self.result
            self.vbox.Replace(old,new)
            old.Destroy()
            self.result = new
            self.Layout()

    def connect(self, connection):
        if self.srv is not None:
            self.srv.close()
        self.srv = sql.Server(connection)
        # print(sql.MetadataCache.servers)

    def _execute_async(self, query):
        result = self.srv.batched_query(query)
        wx.CallAfter(self.set_result, result, self.srv.messages)

    def execute(self):
        query_text = self.texteditor.GetValue()
        result = self.srv.batched_query(query_text)
        self.set_result(result, self.srv.messages)

    def execute_async(self, query):
        self.is_running = True
        self.result.infoBar.ShowMessage("...Running....", wx.ICON_NONE)
        threading.Thread(target=self._execute_async,
                            args=(query,)).start()

    def cancel(self):
        if self.is_running:
            self.srv.cancel()
            self.is_running = False

    def OnKeyDown(self, e):
        # Exec
        if e.GetKeyCode() == wx.WXK_F5 and not self.is_running:
            self.is_running = True
            self.result.infoBar.ShowMessage("...Running....", wx.ICON_NONE)
            query_text = self.texteditor.GetValue()
            threading.Thread(target=self._execute_async,
                             args=(query_text,)).start()
        # cancel
        if e.GetKeyCode() == wx.WXK_ESCAPE and self.is_running:
            self.srv.cancel()
            self.is_running = False

        # propagate the event
        e.ResumePropagation(1)
        e.Skip()


# class Page:
#     def __init__(self, parent, title, id, sqlServer):
#         super().__init__(parent, None, "")
#         self.connection = sqlServer
#         self.id = id
#         self.title = title

class Pager(wx.Panel):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.note_book = wx.Notebook(self)

        self.grids = {}

        self.vbox.Add(self.note_book, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(self.vbox)
        self.Layout()

        self.Show(True)

    # def newPage(self, title, id, sqlServer):
    #     self.grids[id] = Page(self.note_book, title, id, sqlServer)
    #     self.note_book.AddPage(self.grids[id], title, True)


if __name__ == '__main__':
    import sys
    import getopt
    import sql

    class MainFrame(wx.Frame):
        def __init__(self, title):
            wx.Frame.__init__(self, None, title=title, size=(640, 480))
            self.res = QueryEditor(self)

    server = None
    instance = None
    user = None
    password = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "S:I:U:P:")
    except getopt.GetoptError:
        print('sql.py -S Server [-I <Instance>] [-U User] [-P Password]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-S':
            server = arg
        elif opt == '-I':
            instance = arg
        elif opt == '-U':
            user = arg
        elif opt == '-P':
            password = arg

    conn = sql.ConnectionInfo(
        server=server, instance=instance, user=user, password=password)


    

    app = wx.App()

    print(wx.PlatformInformation.Get().GetToolkitMajorVersion())

    frame = MainFrame(title="TdsKit")
    frame.res.connect(conn)

    frame.Show()
    app.MainLoop()
