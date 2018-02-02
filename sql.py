"""SQLServer connection and query"""
from collections import namedtuple
import pytds
import pytds.login

ResultSet = namedtuple("ResultSet", "description data")

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
            self.trusted_security = True

class Server:
    """A connection to a sql server instance"""

    def __init__(self, connection_info: ConnectionInfo):
        self.connection_info = connection_info
        self.messages = None
        self.request_cancel = False
        dsn = self.connection_info.server + "\\" + self.connection_info.instance

        if self.connection_info.trusted_security is True:
            #print("Integrated security" + self.connection_info.server +" " +str(self.connection_info.port) + " " + dsn)
            sspi = pytds.login.SspiAuth(
                server_name=self.connection_info.server,
                port=self.connection_info.port)
            self.conn = pytds.connect(
                dsn=dsn, database=self.connection_info.database, auth=sspi)
        else:
            self.conn = pytds.connect(
                dsn=dsn,
                database=self.connection_info.database,
                user=self.connection_info.user,
                password=self.connection_info.password)

    def close(self):
        if self.conn._closed():
            self.conn.close()

    def cancel(self):
        self.request_cancel = True

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
    conn = ConnectionInfo(server="bt1shx0p", instance="btsqlbcmtst2")
    srv = Server(conn)
    r = srv.query("select '1'")
    print(r)
