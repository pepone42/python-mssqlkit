import pytds
import pytds.login
import resultSet


class SqlServer:
    def __init__(self,
                 server: str,
                 instance: str,
                 database: str = "master",
                 user: str=None,
                 passwd: str =None,
                 IntegratedSecurity: bool=False):
        if IntegratedSecurity is False:
            self.conn = pytds.connect(dsn=server + "\\" + instance,
                                      database=database,
                                      user=user,
                                      password=passwd)
        else:
            p = pytds.login.SspiAuth(server_name=server, port=1433)
            self.conn = pytds.connect(
                dsn=server + "\\" + instance, database=database, auth=p)

    def Close(self):
        self.conn.close()

    def GetCurrentDatabase(self):
        with self.conn.cursor() as cur:
            return cur.execute_scalar("select db_name()")

    def Query(self, sqlQuery: str):
        with self.conn.cursor() as cur:
            resultSets = []
            messages = ""
            try:
                cur.execute(sqlQuery)
            except Exception as e:
                # resultSets.append(resultSet.ResultSet(None,None))
                self.messages = str(e)
                # print("Error: ",type(e)," : ",e)
                return None
            while True:

                description = cur.description

                # TODO:
                # Use fetchMany in a loop and handle cancel event

                # nowNnumber = 0
                # while True:
                #     row = cur.fetchone()
                #     if row == None:
                #         break
                #     gridData.AppendRows()
                #     for i, elem in enumerate(row):
                #         gridData.SetValue(nowNnumber,i,str(elem))
                #     nowNnumber += 1
                try:
                    data = cur.fetchall()
                except Exception as e:
                    print("Error: ", e)
                    data = None

                # print(cur.messages)
                if data is not None:
                    resultSets.append(resultSet.ResultSet(description, data))
                a = cur.nextset()
                # print(a)
                if a is None or a is False:
                    break
            # print(a)
            for m in cur.messages:
                messages = messages + str(m[1]) + "\n"
            self.messages = messages
            if len(resultSets) == 0:
                return None
            return resultSets


if __name__ == '__main__':

    q = SqlServer(server="bt1shx0p", instance="btsqlbcmtst2",
                  database="BCM", IntegratedSecurity=True)

    r = q.Query(
        "select top 1 * from op_operation;select top 10 * from op_operation")

    r = q.Query(
        "select top 1 * f op_operation;select top 10 * from op_operation")

    r = q.Query(
        "select top 1 * from op_operation;print 'tot';\
        select top 10 * from op_operation")
    print(r[0])
    print(q.messages)

    r = q.Query("print 'test'")

    print(q.messages)
    """r = q.Query("select top 10 * from dico_parametre")
    print (r.data)"""
