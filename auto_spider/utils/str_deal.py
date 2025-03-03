# -*- coding: utf-8 -*-
"""
这个脚本的作用是用来处理字符串的一些操作
"""
import re


def replace_strep(instr, default=None, *args):
    """ 这个函数的作用是用来删除字符串中的一些值

    :param instr: 需要处理的字符串
    :param default: 如果不存在那就返回默认值
    :param args: 需要替换的一些值
    :return:

    Example:
    (1)默认会去掉 ['\n', '\t', '\r']
    >>>replace_strep('\\n\thello')
    >>>hello

    (2)自定义去掉 '\n'
    >>>replace_strep('\\n\thello','\\n')
    >>>\thello

    (3)自定义去掉 '\n' '\t'
    >>>replace_strep('\\n\thello','\\n','\t')
    >>>hello
    """
    if not instr:
        return default

    if not args:
        args = ['\n', '\t', '\r', '：']

    for rep in args:
        instr = str(instr).replace(rep, " ")

    return instr.strip()


def re_str_data(patter, data, index=0, default=None):
    """ 这个函数的作用是通过正则来返回需要的结果数据 """
    try:
        result = re.findall(patter, data)
    except Exception as _:
        return default

    if not result:
        return None

    if isinstance(result, (list,)) and index <= len(result):
        return result[index]

    return result


def str_default(s, default=None):
    """ 这个函数的给 str 添加默认的值,如果没有,就填充 None
    :param s: 输入的字符串
    :param default: 输入的默认值
    :return:
    """
    if s:
        return str(s)
    return default
