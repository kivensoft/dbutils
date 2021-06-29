# db.py
"""
扩展的MySQL模块，
"""

import re, pymysql, datetime
from typing import List, Dict

# 数据库操作类
class Connection:
    """ MySQL数据库连接对象 """

    def __init__(self, config: object, showOnly=False):
        """ 创建对象

        config
            包含host,port,user,password,database属性的对象
        showOnly
            True：显示并执行SQL，False：只显示不执行
        """
        self.conn = pymysql.connect(host=config.host, port=config.port,
            user=config.user, password=config.password,
            db=config.database, autocommit=True, #charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)
        self.showOnly = showOnly
    
    def exec(self, sql: str, *args) -> int:
        """ 执行更新语句 """
        cursor = self.conn.cursor()
        try:
            ret = cursor.execute(sql, args)
        finally:
            cursor.close()
        return ret
    
    def query(self, sql: str, *args) -> List[Dict[str, object]]:
        """ 执行查询语句 """
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, args)
            rs = cursor.fetchall()
        finally:
            cursor.close()
        return rs
    
    def close(self) -> None:
        """ 关闭连接 """
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str, *args) -> None:
        """ 在控制台输出要执行的SQL，并根据showOnly标志确定是否执行SQL """
        print(self.parse(sql, *args))
        if not self.showOnly: self.exec(sql, *args)

    @staticmethod
    def parse(sql: str, *args) -> str:
        """ 将带参数的SQL解析成完整的不带参数的可执行SQL
        
        例子：
            "select * from user where username = %s", "tom"
            
            解析后返回
            
            "select * from user where username = 'tom'"
        """
        if not args: return sql
        sv = [-1, args]
        def _toStr(_) -> str:
            sv[0] += 1
            v = sv[1][sv[0]]
            t = type(v)
            return t == int and str(v) or t == str and f"'{v}'" \
                or t == datetime.datetime and f"'{v:%Y-%m-%d %H:%M:%S}'" \
                or t == bool and (v and '1' or '0')
        return re.sub("%s", _toStr, sql)
