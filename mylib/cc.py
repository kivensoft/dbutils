# cc.py
"""
基于colorama的彩色终端显示辅助函数，动态加载
"""

# RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = R, G, Y, B, M, C, W
R = G = Y = B = M = C = W = ''

_enabled = False

def init(enabled: bool) -> None:
    """ 初始化函数, 确定是否启用彩色控制台
    
    enabled
        是否允许彩色控制台
    """
    global R, G, Y, B, M, C, W, _enabled
    if enabled:
        try:
            import colorama
            colorama.init(True)
            _enabled = True
            R, G, Y, B, M, C, W = '\x1b[31m', '\x1b[32m', '\x1b[33m', '\x1b[34m', '\x1b[35m', '\x1b[36m', '\x1b[37m'
        except:
            pass

def p(color: str, fmt: str, *args, end: str ='\n') -> None:
    """ 带色彩的增强型格式化输出到控制台

    color
        指定字体颜色
    fmt_string
        格式化字符串模板
    *args
        格式化字符串模板的不定参数, tuple类型
    end
        换行符, 默认换行, ''表示不换行
    """
    if args: fmt = fmt.format(*args)
    print(fmt if not _enabled else color + fmt, end=end)

if __name__ == '__main__':
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    init(True)
    for x in [R, G, Y, B, M, C, W]:
        p(x, "演示文本")
