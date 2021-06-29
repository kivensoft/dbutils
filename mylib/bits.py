# bits.py
"""
位操作模块，可从16进制字符串获取某一位的标志，在16进制字符串与bool数组中转换
"""

from typing import List

_HEX = "0123456789abcdef"

def getBit(permit: str, index: int) -> bool:
    if index < 0: return permit != None if index == -1 else True
    if not permit or index >= len(permit) << 2: return False
    return (int(permit[index >> 2], 16) & (8 >> (index & 3))) != 0

def setBit(bits: List[bool], index: int, value = True) -> None:
    blen = len(bits)
    if index >= blen: bits.extend(False for i in range(blen, index + 1))
    bits[index] = value

def toList(permit: str) -> List[bool]:
    return [bool(v & x) for v in [int(c, 16) for c in permit] for x in [8, 4, 2, 1]]

def toStr(bits: List[bool]) -> str:
    ret = ""
    if bits:
        blen = len(bits) - 1
        while blen and not bits[blen]: blen -= 1
        blen += 1
        for i in range(blen >> 2):
            bi = i << 2
            ret += _HEX[sum([[8, 4, 2, 1][x] for x in range(4) if bits[bi + x]])]

        if blen & 3:
            ret += _HEX[sum([8, 4, 2, 1][i & 3] for i in range(blen & 0xFFFF_FFFC, blen) if bits[i])]

    return ret

if __name__ == '__main__':
    expectBits = [True, False, True, False, True, False, True, True,
        True, True, False, False, True, True, False, True,
        False, True, False, True, False, True, True, False,
        False, True, True, True, True, False, False, False]
    realBits = toList("abcd5678")
    print("test toBits: ", expectBits == realBits)
    print("test toStr: ", "abcd5678" == toStr(realBits))

    a1 = [True]
    setBit(a1, 3)
    print("test set: ", a1 == [True, False, False, True])

    print("0123 = ",toList("0123"))

    print(toStr([True, False, True, True, True]))
