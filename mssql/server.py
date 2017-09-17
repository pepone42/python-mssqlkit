import pytds
import connectionInfo


class Server:
    """A connection to a sql server instance"""

    def __init__(self, cInfo):
        self.connectionInfo = cInfo
        dsn = self.connectionInfo.server

        if self.connectionInfo.instance is None:
            dsn = dsn + "\\" + self.connectionInfo.instance

        if self.connectionInfo.trustedSecurity is True:
            p = pytds.login.SspiAuth(
                server_name=self.connectionInfo.server,
                port=self.connectionInfo.port)
            self.conn = pytds.connect(
                dsn=dsn, database=self.connectionInfo.database, auth=p)
        else:
            self.conn = pytds.connect(
                dsn=dsn,
                database=self.connectionInfo.database,
                user=self.connectionInfo.user,
                password=self.connectionInfo.password)
