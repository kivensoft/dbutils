# permit.py
"""
智慧社区数据库辅助自动处理工具
Version 0.4.0
Runtime Python 3.6+

Copyright (GPL) 2020-2021 Kiven Lee, <kivensoft@gmail.com>

本工具采用 GPLv2 协议发布, 请在遵循 GPLv2 协议的许可下使用.
依赖包: colorama, pymysql
"""

import sys, argparse
from typing import Callable, List, Dict, Tuple, Optional
from mylib import bits, cc, klib, db

# 缺省值
class DefConfig: 
    host, port, user, password, database = "127.0.0.1", 3306, "root", "password", "cloud_db"

#region 泛型类型定义
Record = Dict[str, object]
Records = List[Record]
RecordDict = List[object, List[Record]]
#endregion

# 定义全局app变量，用于在程序中共享一些全局变量
class App:
    def __init__(self) -> None:
        self.conn: db.Connection = None
app = App()

# 字段常量定义
class C:
    dictId, dictName = "dict_id", "dict_name"
    roleId, permits = "role_id", "permits"
    permitId, permitGroup, permitName = "permit_id", "permit_group", "permit_name"
    permitUrlId, url, ps = "permit_url_id", "url", "ps"
    menuId = "menu_id"

#region 常量定义 
PG_ID_BEGIN = 3000
PG_ID_END = 4000
GROUPS_SQL = f"select * from t_dict where dict_id >= {PG_ID_BEGIN} and dict_id < {PG_ID_END} order by dict_id"
PERMITS_SQL = "select * from t_permit where permit_id >= 0 order by permit_id"
PERMIT_URLS_SQL = "select * from t_permit_url order by permit_url_id"
ROLES_SQL = "select * from t_role order by role_id"
MENU_SQL = "select menu_id, permit_id from t_menu"
UPD_DICT_SQL = "update t_dict set dict_name=%s where dict_id=%s"
UPD_PERMIT_SQL = "update t_permit set permit_group=%s where permit_id=%s"
UPD_PERMIT_ID_SQL = "update t_permit set permit_id=%s where permit_id=%s"
UPD_PERMIT_ALL_SQL = "update t_permit set permit_group=%s, permit_name=%s where permit_id=%s"
UPD_PERMIT_URL_SQL = "update t_permit_url set permit_id=%s where permit_url_id=%s"
UPD_ROLE_SQL = "update t_role set permits=%s where role_id=%s"
UPD_MENU_SQL = "update t_menu set permit_id=%s where menu_id=%s"
#endregion

# 权限组自动紧凑排序
def sortDict(conn: db.Connection) -> None:
    dicts = conn.query(GROUPS_SQL)
    permits = conn.query(PERMITS_SQL)

    for i, v in enumerate(dicts):
        expectId, realId = i + PG_ID_BEGIN, v[C.dictId]
        if expectId == realId: continue

        # 不是按序号递增，进行处理
        conn.execute("update t_dict set dict_id=%s where dict_id=%s", expectId, realId)

        # 处理关联的t_permit表
        pgid = realId - PG_ID_BEGIN
        for p in permits:
            if p[C.permitGroup] == pgid:
                conn.execute("update t_permit set permit_group=%s where permit_id=%s", i, p[C.permitId])
        print("")

# 权限组手动排序
def runDict(conn: db.Connection) -> None:
    while True:
        dicts, permits = conn.query(GROUPS_SQL), conn.query(PERMITS_SQL)

        if not isCompactRecords(dicts, C.dictId):
            cc.p(cc.R, "权限组不是紧凑排序模式，请先进行紧凑排序!")
            return

        # 输出现有分组列表
        print(f"{cc.M}idx\t{cc.Y}id\t{cc.G}name")
        print("=" * 80)
        for i, v in enumerate(dicts):
            print(f"{cc.M}{i}\t{cc.Y}{v[C.dictId]}\t{cc.G}{v[C.dictName]}")
        print("")

        cmd = inputCmd()
        if cmd == "quit": return
        else:
            ids = parseCmd(cmd, len(dicts) - 1)
            if ids:
                print("")
                moveItem(ids, dicts, lambda old, new_, _: moveDictItem(old, new_, permits, conn))

        input("\n输入回车键继续: ")

# 权限组移动回调函数
def moveDictItem(oldDict: Record, newDict: Record, permits: Records, conn: db.Connection) -> None:
    conn.execute(UPD_DICT_SQL, newDict[C.dictName], oldDict[C.dictId])

    old_gid, new_gid = oldDict[C.dictId] - PG_ID_BEGIN, newDict[C.dictId] - PG_ID_BEGIN
    for p in permits:
        if new_gid == p[C.permitGroup]:
            conn.execute(UPD_PERMIT_SQL, old_gid, p[C.permitId])
    print("")

# 权限自动紧凑排序
def sortPermit(conn: db.Connection) -> None:
    permits = conn.query(PERMITS_SQL)
    permitUrlDict = klib.groupby(conn.query(PERMIT_URLS_SQL), lambda x: x[C.permitId])
    roles = conn.query(ROLES_SQL)

    for r in roles: r[C.ps] = bits.toList(r[C.permits])

    idx = permits[0][C.permitId]
    for v in permits:
        oldId = v[C.permitId]
        if idx != oldId:
            conn.execute(UPD_PERMIT_ID_SQL, idx, oldId)
            changeRoles(roles, oldId, idx)
            updateRelation(permitUrlDict, oldId, lambda x: conn.execute(UPD_PERMIT_URL_SQL, idx, x[C.permitUrlId]))
            print("")
        idx += 1
    saveRoles(conn, roles)

# 权限手动排序
def runPermit(conn: db.Connection) -> None:
    while True:
        dicts, permits, roles = conn.query(GROUPS_SQL), conn.query(PERMITS_SQL), conn.query(ROLES_SQL)
        permitUrlDict = klib.groupby(conn.query(PERMIT_URLS_SQL), lambda x: x[C.permitId])
        menuDict = klib.groupby(conn.query(MENU_SQL), lambda x: x[C.permitId])

        for r in roles: r[C.ps] = bits.toList(r[C.permits])

        # 校验是否紧凑排序
        if not isCompactRecords(permits, C.permitId):
            print("权限不是紧凑排序模式，先进行紧凑排序!")
            return

        # 输出分组排序列表
        for d in dicts:
            print("[{}] {}{}".format(d[C.dictId], cc.Y, d[C.dictName]))
            pg = d[C.dictId] - PG_ID_BEGIN
            for p in permits:
                if pg == p[C.permitGroup]:
                    print(f"    {cc.G}{p[C.permitId]:3} {cc.C}{p[C.permitName]}")

        cmd = inputCmd()
        if cmd == "quit": return
        else:
            ids = parseCmd(cmd, len(permits) - 1)
            if ids:
                print("")
                moveItem(ids, permits, lambda old, new_, flag: movePermitItem(old, new_, permitUrlDict, menuDict, roles, conn, not flag))
                saveRoles(conn, roles)

        input("\n输入回车键继续: ")

# 通用更新关联记录函数，通过回调函数进行具体处理
def updateRelation(dict_: RecordDict, key: object, callback: Callable[[Record], object]):
    list_ = dict_.get(key)
    if list_:
        for item in list_: callback(item)

# 对角色的权限按权限索引的变动进行变动
def changeRoles(roles: Records, oldPermit: int, newPermit: int, clearOld: bool = True):
    if oldPermit < 0 or newPermit < 0: return
    for r in roles:
        ps = r[C.ps]
        b = bits.getBit(r[C.permits], oldPermit)
        if clearOld: bits.setBit(ps, oldPermit, False)
        bits.setBit(ps, newPermit, b)

# 将角色变化后的权限写入数据库
def saveRoles(conn: db.Connection, roles: Records) -> None:
    first = True
    for r in roles:
        newPermits = bits.toStr(r[C.ps])
        if newPermits != r[C.permits]:
            if first:
                first = False
                print("")
            conn.execute(UPD_ROLE_SQL, newPermits, r[C.roleId])

# 显示输入命令
def inputCmd() -> None:
    print("命令示例:")
    print(f"    移动索引，从位置2移动到位置1: {cc.M}2 1")
    print(f"    移动索引，从位置1移动到位置3: {cc.M}1 3")
    print(f"    退出应用程序: {cc.M}quit")
    return input("输入命令: ")

# 解析用户输入的命令
def parseCmd(cmd: str, maxIndex: int) -> Optional[Tuple[int, int]]:
    cmds = cmd.split()
    if len(cmds) != 2:
        cc.p(cc.R, "命令格式错误!")
        return None
    ids = [int(x) for x in cmds]
    if ids[0] > maxIndex or ids[1] > maxIndex or ids[0] == ids[1]:
        cc.p(cc.R, "索引范围无效!")
        return None
    return (ids[0], ids[1])

# 移动权限回调函数
def movePermitItem(oldPermit: Record, newPermit: Record, permitUrlDict: RecordDict,
                menuDict: RecordDict, roles: Records, conn: db.Connection, clearOld: bool = True) -> None:

    oldId, newId = oldPermit[C.permitId], newPermit[C.permitId]

    # 更新角色权限的变化
    changeRoles(roles, newId, oldId, clearOld)
    conn.execute(UPD_PERMIT_ALL_SQL, newPermit[C.permitGroup], newPermit[C.permitName], oldId)

    # 更新关联的t_permit_url
    updateRelation(permitUrlDict, newId, lambda x: conn.execute(UPD_PERMIT_URL_SQL, oldId, x[C.permitUrlId]))
    # 更新关联的t_menu
    updateRelation(menuDict, newId, lambda x: conn.execute(UPD_MENU_SQL, oldId, x[C.menuId]))
    print("")

# 移动列表中的项到指定位置
def moveItem(pos: Tuple[int, int], records: Records, callback: Callable[[Record, Record, bool], None]) -> None:
    """ 移动records中的项，从ifrom到ito"""
    if pos[0] > pos[1]:
        for i in range(pos[0], pos[1], -1):
            callback(records[i], records[i - 1], False)
        callback(records[pos[1]], records[pos[0]], True)
    else:
        for i in range(pos[0], pos[1] - 1, 1):
            callback(records[i], records[i + 1], False)
        callback(records[pos[1] - 1], records[pos[0]], True)

# 判断记录集是否紧凑排序
def isCompactRecords(records: Records, key: str) -> bool:
    if records:
        idx = records[0][key]
        for r in records:
            if idx != r[key]: return False
        idx += 1
    return True

# 解析命令行参数
def initArgs():
    """ 初始化命令行参数 """
    parse = argparse.ArgumentParser(add_help=False, description='权限调整工具')
    parse.add_argument("-h", "--help", action="store_true", help="打印帮助信息并退出")
    parse.add_argument("--no-colorama", action="store_true", required=False, help="不使用彩色控制台", default=False)
    parse.add_argument("--host", required=False, help=f"数据库服务器地址, 缺省为: {DefConfig.host}", default=DefConfig.host)
    parse.add_argument("--port", required=False, help=f"数据库服务器端口, 缺省为: {DefConfig.port}", default=DefConfig.port)
    parse.add_argument("-u", "--user", required=False, help=f"数据库用户名, 缺省为: {DefConfig.user}", default=DefConfig.user)
    parse.add_argument("-p", "--password", required=False, help=f"数据库口令, 缺省为: {DefConfig.password}", default=DefConfig.password)
    parse.add_argument("-d", "--database", required=False, help=f"数据库名称, 缺省为: {DefConfig.database}", default=DefConfig.database)
    parse.add_argument("--sort-dict", action="store_true", default=False, help="权限组进行紧凑排序")
    parse.add_argument("--sort-permit", action="store_true", default=False, help="权限进行紧凑排序")
    parse.add_argument("--permit", action="store_true", default=False, help="权限排序")
    parse.add_argument("--exec", action="store_true", default=False, help="执行sql")

    #解析命令行参数并返回结果
    _opts = parse.parse_args()
    if _opts.help:
        parse.print_help()
        sys.exit(0)
    return _opts

# 脚本入口点
if __name__ == '__main__':
    opts = initArgs()
    if not opts.no_colorama: cc.init(True)
    conn = db.Connection(opts, not opts.exec)
    if opts.sort_dict:
        sortDict(conn)
    elif opts.sort_permit:
        sortPermit(conn)
    elif opts.permit:
        runPermit(conn)
    else:
        runDict(conn)
    conn.close()
