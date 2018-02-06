"""SQLServer connection and query"""

import platform

from collections import namedtuple
import pytds
import pytds.login


ResultSet = namedtuple("ResultSet", "description data")
Metadata = namedtuple("Metadata",("Databases",  "UserTypes", "Objects"))

class ConnectionInfo:
    """Describe how to connect to a sql server instance"""

    def __init__(self, server: str, instance: str=None, port: int = 1433,
                 database: str = "master", user: str = None, password: str = None):
        self.server = server
        self.instance = instance
        self.port = port
        self.user = user
        self.database = database
        self.password = password
        self.trusted_security = False
        if self.user is None:
            if platform.system() == 'Windows':
                print("Using windows authentication")
                self.trusted_security = True
            else:
                raise Exception("trusted security unsupported")



class MetadataCache:
    """ cache metadata for a server """

    def __init__(self):
        self.servers = {}

    def new_server(self, connection_info: ConnectionInfo):
        self.dsn = connection_info.server
        if connection_info.instance is not None:
            dsn = connection_info.server + "\\" + connection_info.instance
        if dsn not in self.servers:
            srv = Server(connection_info)
            databases = srv.get_databases()
            user_types = srv.get_user_types()
            self.servers[dsn] = Metadata(databases, user_types, None)
            srv.close()

class Server:
    """A connection to a sql server instance"""

    def __init__(self, connection_info: ConnectionInfo):
        self.connection_info = connection_info
        self.messages = None
        self.request_cancel = False
        self._databases = None
        self._user_types = None
        dsn = None
        if self.connection_info.instance is not None:
            dsn = self.connection_info.server + "\\" + self.connection_info.instance

        if self.connection_info.trusted_security is True:
            #print("Integrated security" + self.connection_info.server +" " +str(self.connection_info.port) + " " + dsn)
            sspi = pytds.login.SspiAuth(
                server_name=self.connection_info.server,
                port=self.connection_info.port)
            if dsn is not None:
                self.conn = pytds.connect(
                    dsn=dsn, database=self.connection_info.database, auth=sspi)
            else:
                self.conn = pytds.connect(
                    server=self.connection_info.server, database=self.connection_info.database, auth=sspi)
        else:
            if dsn is not None:
                self.conn = pytds.connect(
                    dsn=dsn,
                    database=self.connection_info.database,
                    user=self.connection_info.user,
                    password=self.connection_info.password)
            else:
                self.conn = pytds.connect(
                    server=self.connection_info.server,
                    database=self.connection_info.database,
                    user=self.connection_info.user,
                    password=self.connection_info.password)


    def close(self):
        if not self.conn._closed:
            self.conn.close()

    def cancel(self):
        self.request_cancel = True

    def get_database(self):
        with self.conn.cursor() as cur:
            return cur.execute_scalar('select db_name()')

    def get_databases(self):
        if self._databases is None:
            res = self.query("SELECT name FROM master.sys.databases")
            self._databases = list(map(lambda r: r[0],res[0].data))
        return self._databases

    def get_user_types(self):
        if self._user_types is None:
            types = {}
            for db in self.get_databases():
                types[db] = {}
                res = self.query("SELECT name,user_type_id FROM ["+db+"].sys.types")
                for r in res[0].data:
                    types[db][r[1]]=r[0]
            self._user_types = types
        return self._user_types

    def query(self, sql):
        """execute the sql query and return an array of resultset"""

        with self.conn.cursor() as cur:
            result_sets = []
            messages = ""
            try:
                cur.execute(sql)
            except Exception as ex:
                self.messages = str(ex)
                return None
            while True:

                description = cur.description

                try:
                    data = cur.fetchmany(10000)
                    while True:
                        d = cur.fetchmany(10000)
                        if d is None or len(d) == 0:
                            break
                        if self.request_cancel:
                            cur.cancel()
                            self.request_cancel = False
                        data = data + d
                except Exception as ex:
                    data = None


                if data is not None:
                    result_sets.append(ResultSet(description, data))

                have_more_set = cur.nextset()
                if have_more_set is None or have_more_set is False:
                    break

            for msg in cur.messages:
                messages = messages + str(msg[1]) + "\n"
            self.messages = messages

            if not result_sets:
                return None
            return result_sets

if __name__ == '__main__':
    import sys, getopt
    
    server = None
    instance = None
    user = None
    password = None
    try:
        opts, args = getopt.getopt(sys.argv[1:],"S:I:U:P:")
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
    print("Server "+str(server))
    print("Instance "+str(instance))
    print("User "+str(user))
    print("Password "+str(password))
    conn = ConnectionInfo(server=server, instance = instance ,user = user, password= password)
    srv = Server(conn)
    r = srv.query("select '1'")
    print(r)


