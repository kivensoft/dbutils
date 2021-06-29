# klib.py
"""
辅助函数工具模块
"""

import time
from datetime import datetime, timedelta
from typing import Union, Optional, List, Dict, Callable, TypeVar

TZ_OFFSET = timedelta(seconds=time.timezone)
DT = "%Y-%m-%d %T"
_MAX_DAY_OF_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

T = TypeVar('T')  # Any type.
KT = TypeVar('KT')  # Key type.
VT = TypeVar('VT')  # Value type.

def localToUtc(value: datetime) -> datetime:
    """ 本地时间转成UTC时间 """
    return value + TZ_OFFSET

def utcToLocal(value: datetime) -> datetime:
    """ UTC时间转成本地时间 """
    return value - TZ_OFFSET

def parseDateTime(value: str) -> Optional[datetime]:
    """ 时间字符串解析成datetime格式 """
    if not value: return None
    if value.find("T") != -1 and value.find("Z") != -1:
        d = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ") - TZ_OFFSET
    else:
        d = datetime.fromisoformat(value)
        if d.tzinfo:
            d -= d.tzinfo.utcoffset(d) + TZ_OFFSET
    return d

def addDays(value: datetime, days: int = 1) -> datetime:
    return value + timedelta(days=days)

def IsLeapYear(year: int) -> bool:
    """ 计算年份是否属于闰年 """
    # 非世纪年能被4整除，且不能被100整除的是闰年
    # 世纪年能被400整除的是闰年
    return not (year & 3) and year % 100 or not (year % 400)

def getDaysOfYear(year: int) -> int:
    """ 获取指定年份的天数 """
    return IsLeapYear(year) and 366 or 365

def getDaysOfMonth(year: int, month: int) -> int:
    """ 获取指定年月的天数 """
    if month == 2:
        return IsLeapYear(year) and 29 or 28
    else:
        return _MAX_DAY_OF_MONTH[month - 1]

def addMonths(value: datetime, months: int = 1) -> datetime:
    """ 计算增加指定月份后的日期 """
    y, m, d = value.year, value.month, value.day
    oldMax = getDaysOfMonth(y, m)
    m += months
    y += (m - 1) // 12
    m = ((m - 1) % 12) + 1
    newMax = getDaysOfMonth(y, m)
    if oldMax == d or d > newMax:
        d = newMax
    return datetime(y, m, d, value.hour, value.minute, value.second, value.microsecond)

def addYears(value: datetime, years: int = 1) -> datetime:
    """ 计算增加指定年份后的日期 """
    y, m, d = value.year, value.month, value.day
    oldMax = getDaysOfMonth(y, m)
    y += years
    newMax = getDaysOfMonth(y, m)
    if oldMax == d or d > newMax:
        d = newMax
    return datetime(y, m, d, value.hour, value.minute, value.second, value.microsecond)

def groupby(list_: List[T], getKey: Callable[[T], KT], getItem: Callable[[T], VT] = None) -> Dict[KT, List[VT]]:
    """
    返回将列表转成按指定键分组的字典

    list_:      源列表
    getKey:     获取键的回调函数
    getItem:    获取值的回调函数
    """
    ret = {}
    for v in list_:
        key = getKey(v)
        item = getItem and getItem(item) or v
        value = ret.get(key)
        if value == None: ret[key] = [item]
        else: value.append(item)
    return ret