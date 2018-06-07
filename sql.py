"""SQLServer connection and query"""

import platform

from collections import namedtuple
import pytds
import pytds.login


ResultSet = namedtuple("ResultSet", "description data")
Metadata = namedtuple("Metadata",("Databases",  "SysTypes", "Objects"))

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
    servers = {}

    @staticmethod
    def new_server(dsn, databases, sys_types):
        if dsn not in MetadataCache.servers:
            MetadataCache.servers[dsn] = Metadata(databases, sys_types, None)
            print("New server" + str(MetadataCache.servers[dsn]))

class Server:
    """A connection to a sql server instance"""

    def __init__(self, connection_info: ConnectionInfo):
        self.connection_info = connection_info
        self.messages = None
        self.request_cancel = False
        self._databases = None
        self._sys_types = None
        self.dsn = connection_info.server
        self.cur = None
        if self.connection_info.instance is not None:
            self.dsn = self.connection_info.server + "\\" + self.connection_info.instance

        if self.connection_info.trusted_security is True:
            #print("Integrated security" + self.connection_info.server +" " +str(self.connection_info.port) + " " + dsn)
            sspi = pytds.login.SspiAuth(
                server_name=self.connection_info.server,
                port=self.connection_info.port)
            if self.connection_info.instance is not None:
                self.conn = pytds.connect(
                    dsn=self.dsn, database=self.connection_info.database, auth=sspi)
            else:
                self.conn = pytds.connect(
                    server=self.connection_info.server, database=self.connection_info.database, auth=sspi)
        else:
            if self.connection_info.instance is not None:
                self.conn = pytds.connect(
                    dsn=self.dsn,
                    database=self.connection_info.database,
                    user=self.connection_info.user,
                    password=self.connection_info.password)
            else:
                self.conn = pytds.connect(
                    server=self.connection_info.server,
                    database=self.connection_info.database,
                    user=self.connection_info.user,
                    password=self.connection_info.password)
        MetadataCache.new_server(self.dsn, self._get_databases(), self._get_sys_types())

    def close(self):
        if not self.conn._closed:
            self.conn.close()

    def cancel(self):
        if self.cur:
            try:
                self.cur.cancel()
            except:
                print("Who cares")
                pass
            self.messages = "Canceld"
            self.cur = None
            self.request_cancel = True

    def get_database(self):
        with self.conn.cursor() as cur:
            return cur.execute_scalar('select db_name()')

    def _get_databases(self):
        if self._databases is None:
            res = self.query("SELECT name FROM master.sys.databases")
            self._databases = list(map(lambda r: r[0],res[0].data))
        return self._databases

    def _get_sys_types(self):
        if self._sys_types is None:
            types = {}
            res = self.query("SELECT name,type FROM [master].sys.systypes UNION SELECT NAME, user_type_id FROM master.sys.types")
            for r in res[0].data:
                types[r[1]]=r[0]
            self._sys_types = types
        return self._sys_types

    def metadata(self):
        if self.dsn in MetadataCache.servers:
            return MetadataCache.servers[self.dsn]
        return None

    def _better_description(self, desc):
        type_id = desc[1]
        hr_type = "??"
        if type_id in self.metadata().SysTypes:
            hr_type = self.metadata().SysTypes[type_id]
        print(str(desc) + "=" + hr_type)
        return hr_type

    def query(self, sql):
        """execute the sql query and return an array of resultset"""

        with self.conn.cursor() as cur:
            self.cur = cur
            result_sets = []
            self.messages = ""
            messages = ""
            self.request_cancel = False
            try:
                cur.execute(sql)
            except Exception as ex:
                self.cur = None
                self.messages = str(ex)
                return None
            while True:
                try:
                    description = cur.description
                except:
                    self.messages = "Error reading description"
                if self.metadata() is not None and description is not None:
                    description = list(map(lambda c: c+(self._better_description(c),),description))
                    print(description)
                try:
                    # data = cur.fetchmany(10000)
                    # while True:
                    #     d = cur.fetchmany(10000)
                    #     if d is None or len(d) == 0:
                    #         break
                    #     if self.request_cancel:
                    #         cur.cancel()
                    #         self.request_cancel = False
                    #     data = data + d
                    data = cur.fetchall()
                except Exception as ex:
                    data = None
                    self.messages = "Error while fetching data"
                    break



                if data is not None:
                    result_sets.append(ResultSet(description, data))

                try:
                    have_more_set = cur.nextset()
                except:
                    self.messages = "Error reading next set"
                    break
                if have_more_set is None or have_more_set is False:
                    break

            try:
                for msg in cur.messages:
                    messages = messages + str(msg[1]) + "\n"
            except:
                self.messages = "Error reading messages"
            self.messages = messages + self.messages

            print("End ",str(len(result_sets)))

            self.cur = None

            if not result_sets:
                return None
            return result_sets
        
    def script_object(self, schema_name, object_name):
        query = '''
        declare @script varchar(max),@objectname varchar(500), @schemaname varchar(64);
        select @script = '', @objectname = '$OBJECTNAME$', @schemaname = '$SCHEMANAME$';
        select @script +=def from (
        select
        'USE ['+db_name()+']
        GO
        /****** Object:  StoredProcedure ['+schema_name(schema_id)+'].['+name+']    Script Date: '+convert(varchar,getdate())+' ******/
        SET ANSI_NULLS ON
        GO
        SET QUOTED_IDENTIFIER ON
        GO
        '
        + OBJECT_DEFINITION(object_id) def from sys.objects where name = @objectname and schema_name(schema_id) = @schemaname
        union all
        select 
        'GO
        /****** Object:  NumberedStoredProcedure ['+schema_name(schema_id)+'].['+a.name+'];'+convert(varchar,b.procedure_number)+'    Script Date: '+convert(varchar,getdate())+' ******/
        SET ANSI_NULLS ON
        GO
        SET QUOTED_IDENTIFIER ON
        GO
        ' 
        + b.definition from sys.objects a
        join sys.numbered_procedures b on a.object_id=b.object_id
        where a.name = @objectname and schema_name(a.schema_id) = @schemaname
        ) a 
        select @script
        '''
        query = query.replace("$OBJECTNAME$", object_name)
        if schema_name is None:
            schema_name='dbo'
        query = query.replace("$SCHEMANAME$", schema_name)
        print(query)
        
        return self.query(query)[0].data[0][0]

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
    r = srv.query("use bcm")
    print(r)
    print(srv.get_database())
    r = srv.script_proc("dbo","Dico_SelectOptimNetworkTable")
    print(r)
    print(srv.messages)


