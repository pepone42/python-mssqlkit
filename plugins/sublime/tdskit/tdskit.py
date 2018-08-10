import sublime
import sublime_plugin
import xmlrpc.client
import re

class tdskit(object):
    xmlrpcclient = xmlrpc.client.ServerProxy('http://127.0.0.1:8000', allow_none=True)



def plugin_unloaded():
    print("PluginUnLoaded")


def get_settings(key, default_value=None):
    settings = sublime.load_settings('tdskit.sublime-settings')
    return settings.get(key, default_value)

def is_connected(view):
    print("Is_connected?")
    try:
        if view.settings().get("tds_connection_info") is not None:
            print("Try ping")
            tdskit.xmlrpcclient.ping()
            return True
        print("No")
        return False
    except:
        print("No")
        view.settings().set("tds_connection_info",None)
        return False

#def tds_connect(view, server, instance, db, user, password):
def tds_connect(view, connection_info):
    c = connection_info
    view.settings().set("tds_connection_info",c)
    tdskit.xmlrpcclient.connect(view.id(), c["Server"], c.get("Instance"), c.get("DefaultDatabase"), c.get("User"), c.get("Password"))
    #view.settings.set("tds_connection_info", {"Server": server, "Instance": instance, "DefaultDatabase": db, "User": user, "Password": password})
    #print("Conn info " + str(view.tds_connection_info))


class tds_insert_bufferCommand(sublime_plugin.TextCommand):

    def run(self, edit, position, text):
        # Command to output text on the outut console
        self.view.insert(edit, position, text)


class tds_connectCommand(sublime_plugin.TextCommand):
    lists = []

    def run(self, edit):
        # build a connections list from the connections settings
        connections = get_settings("Connections", None)
        self.lists = []
        for con in connections:
            self.lists.append([con["Name"]])
        sublime.active_window().show_quick_panel(self.lists, self.on_chosen)

    def on_chosen(self, index):
        if (index >= 0):
            print(str(self.lists[index]))
            con = get_settings("Connections", None)[index]
            print(str(con))
            # self.view.settings().set("tds_connection_info",con)
            # tdskit.xmlrpcclient.connect(self.view.id(), con["Server"], con["Instance"], con["DefaultDatabase"])
            tds_connect(self.view,con)


def get_selection_or_all(view):
    # return the first region selected, or all the file otherwise
    if view.sel()[0]:
        # Get the selected text
        s = view.substr(view.sel()[0])
    else:
        # Get all Region
        s = view.substr(sublime.Region(0, view.size()))
    return s


class tds_queryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if is_connected(self.view):
            tdskit.xmlrpcclient.exec_query_async(self.view.id(), get_selection_or_all(self.view))


class tds_cancel_queryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if is_connected(self.view):
            tdskit.xmlrpcclient.cancel(self.view.id())


class tds_script_objectCommand(sublime_plugin.TextCommand):

    re_with_sch = re.compile(r'^([^.\s]+)\.([^.\s]+)$')
    # re_without_sch = re.compile(r'^([^\.\s]+)$')

    def open_in_new_view(self, identifier, text):
        v = sublime.active_window().new_file()
        sublime.active_window().focus_view(v)
        v.run_command('tds_insert_buffer', {'position': 0, 'text': text})
        v.set_syntax_file(self.view.settings().get('syntax'))
        v.set_name(identifier + '.sql')
        # print(v.settings().get("tds_connection_info"))
        con = self.view.settings().get("tds_connection_info")
        # v.settings().set("tds_connection_info",con)
        tds_connect(v, con)
        tdskit.xmlrpcclient.switch_to(v.id())
        # connect_to_database(v, sqlview.connectionString,sqlview.connectionName)

    def run(self, edit):
        if is_connected(self.view):
            if self.view.sel()[0]:
                s = self.view.substr(self.view.sel()[0])
                m = self.re_with_sch.match(s)

                if m:
                    sch = m.group(1)
                    obj = m.group(2)

                    # print(tdskit.xmlrpcclient.script_object(self.view.id(), sch, obj))
                    self.open_in_new_view(s, tdskit.xmlrpcclient.script_object(self.view.id(), sch, obj))
                else:
                    # print(tdskit.xmlrpcclient.script_object(self.view.id(), None, s))
                    self.open_in_new_view(s, tdskit.xmlrpcclient.script_object(self.view.id(), None, s))


class MyEvents(sublime_plugin.EventListener):

    def on_close(self, view):
        if is_connected(view):
            tdskit.xmlrpcclient.delete_view(view.id())

    def on_activated(self, view):
        if is_connected(view):
            tdskit.xmlrpcclient.switch_to(view.id())