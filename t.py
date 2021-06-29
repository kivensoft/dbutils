import pymysql
from typing import Dict, List, Any

class DefaultDB: 
    host, port, user, password, database = "127.0.0.1", 3306, "root", "password", "cloud_db"

class Connection:
    def __init__(self, config):
        self._conn = pymysql.connect(host=config.host, port=config.port,
            user=config.user, password=config.password,
            db=config.database, #charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)
        # self.today = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    
    def exec(self, sql: str, *args) -> None:
        cursor = self._conn.cursor()
        cursor.execute(sql, args)
        cursor.close()
        self._conn.commit()

    def query(self, sql: str, *args) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(sql, args)
        rs = cursor.fetchall()
        cursor.close()
        return rs
    
    def close(self) -> None:
        self._conn.close()

conn = Connection(DefaultDB)
a = conn.query("select * from t_user")
print(type(a[0]))
for i in a:
    print(i)