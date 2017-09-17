class ConnectionInfo:
    """Describe how to connect to a sql server instance"""

    def __init__(self, server, instance, port=1433, database="master", user=None, password=None):
        self.server = server
        self.instance = instance
        self.port = port
        self.user = user
        self.database = database
        self.password = password
        if self.user is None:
            self.trustedSecurity = True
