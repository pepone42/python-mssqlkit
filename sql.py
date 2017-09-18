"""SQLServer connection and query"""
from collections import namedtuple
import pytds

ResultSet = namedtuple("ResultSet", "description data")

class ConnectionInfo:
    """Describe how to connect to a sql server instance"""

    def __init__(self, server, instance, port=1433, database="master", user=None, password=None):
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

    def __init__(self, connection_info):
        self.connection_info = connection_info
        self.messages = None
        dsn = self.connection_info.server

        if self.connection_info.instance is None:
            dsn = dsn + "\\" + self.connection_info.instance

        if self.connection_info.trustedSecurity is True:
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

    def query(self, sql):
        """execute the sql query and return an array of resultset"""

        with self.conn.cursor() as cur:
            result_sets = []
            messages = ""
            try:
                cur.execute(sql)
            except Exception as ex:
                # result_sets.append(resultSet.ResultSet(None,None))
                self.messages = str(ex)
                # print("Error: ",type(e)," : ",e)
                return None
            while True:

                description = cur.description

                try:
                    data = cur.fetchall()
                except Exception as ex:
                    print("Error: ", ex)
                    data = None

                # print(cur.messages)
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
