# -*- coding: utf-8 -*-
"""
这个脚本的作用是用来处理一些公共的东西
"""
import asyncio
import datetime
import hashlib
import html
import json
import re
import time

import math
import uuid

from retrying import retry

from oversea_mall.settings import DM_SCHEDULER_URL
import aiohttp
# import mmh3
# import pytz


def round_fmt(f):
    f = str(f - f % 0.0001)
    if len(f) > 4:
        end = f.find('.')
        return float(f[:end + 3])
    else:
        return float(f)


def gen_session_id():
    # alph = string.ascii_lowercase
    # number = string.digits
    # ret = ''.join(random.choice(alph + number) for _ in range(length))
    ret = uuid.uuid4().hex
    return ret


def gen_md5(str_con):
    """ 把输入的数据转换成MD5
    :param str_con: 输入的数据
    :return:
    """
    hl = hashlib.md5()
    hl.update(str(str_con).encode(encoding='utf-8'))
    return hl.hexdigest()


def slice_arr(arr, slice_len):
    """ 把数组按照给定的长度切割
    :param arr: 数组
    :param slice_len: 给定的长度
    :return:
    Example:
        Input:
            arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            slice_len = 3
        Output:
            [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11]]
    """
    return [
        arr[x * slice_len:(x + 1) * slice_len]
        for x in range(0, math.ceil(len(arr) / slice_len))
    ]


def get_now_datetime():
    """这个函数的作用是返回当前的时间 %Y-%m-%d %H:%M:%S """
    today = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return today


def get_now_date(day=0):
    """这个函数的作用是返回当前的时间 %Y-%m-%d """
    i = datetime.datetime.now() + datetime.timedelta(days=day)
    return i.strftime('%Y-%m-%d')


def get_index_arr(arr, index=0, default=None):
    """ 这个函数的作用是根据 index 获取数组中的元素
    :param arr: 数组
    :param index: 数组中的索引位置
    :param default: 默认填充值
    :return:
    """
    if not arr:
        return default

    if not isinstance(arr, (list, tuple)):
        return default

    if index >= len(arr):
        return default

    text = arr[index]
    if text in [None, '']:
        return default
    else:
        if isinstance(text, (bytes,)):
            return text.decode('utf-8').strip()
        return text


def replace_none(arr, default=None):
    """ 这个函数的作用是替换调数组中的空值与空串
    :param arr: 需要替换的数组
    :param default: 默认的替换值
    :return:
    """
    return list(map(lambda x: default if x in [None, ''] else x, arr))


def spider_name(name: str):
    """ 这个函数的作用是用来处理 spider name """
    if ":" not in name:
        return name

    return get_index_arr(name.split(":"), -1)


def get_now_time():
    return time.strftime('%m%d-%H%M', time.localtime(time.time()))


# def timestamp_str(timestamp):
#     """时间戳转换时间字符串"""
#     return datetime.datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')


def url2dict(url):
    query = {i.split('=')[0]: i.split('=')[1] for i in url.split('?')[1].split('&')}
    return query


def aby_proxy():
    proxy_host = "http-dyn.abuyun.com"
    proxy_port = "9020"

    # 代理隧道验证信息
    proxy_user = "HAZ8395D9E0I92DD"
    proxy_pass = "F087B0CEFCAB6B0A"

    proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": proxy_host,
        "port": proxy_port,
        "user": proxy_user,
        "pass": proxy_pass,
    }

    proxies = {
        "http": proxy_meta,
        "https": proxy_meta,
    }
    return proxies


def partition(ls, size):
    """
    Returns a new list with elements
    of which is a list of certain size.

        >>> partition([1, 2, 3, 4], 3)
        [[1, 2, 3], [4]]
    """
    return [ls[i:i + size] for i in range(0, len(ls), size)]


def del_dict_none_field(item: dict):
    """删除字典中空字段"""
    for key in list(item.keys()):
        if not item.get(key):
            del item[key]
    return item


def judge_in(examples: list, party: list or str, allin=False):
    for example in examples:
        if allin:
            if example in party:
                continue
            else:
                return False
        else:
            if example in party:
                return True
    if allin:
        return True
    else:
        return False


# def murmurhash2ts(ua, num):
#     temp = ('["{}","zh-CN",24,-480,true,true,true,"undefined","function",null,"MacIntel",8,8,null,"Chrome PDF Plu'
#             'gin::Portable Document Format::application/x-google-chrome-pdf~pdf;Native Client::::application/x-nac'
#             'l~,application/x-pnacl~",{}]')
#     array_str = temp.format(ua, num)
#     array = json.loads(array_str)  # type: list
#     print(array)
#     s = ''
#     repl = {
#         "True": "true",
#         "False": "false",
#         "None": ""
#     }
#     for index, item in enumerate(array):
#         if str(item) in list(repl.keys()):
#             ele = repl[str(item)]
#         else:
#             ele = str(item)
#         # ele = str(item)
#         if index == 0:
#             s += ele
#         else:
#             s += "###" + ele
#
#     print(s)
#     r = mmh3.hash(s, 31)
#     if r < 0:
#         return 4294967295 & r
#
#     return mmh3.hash(s, 31)


def sales2int(sales:str) -> int:
    sales = sales.replace('+', '')
    if '万' in sales:
        sales = float(sales.replace('万', '')) * 10000
    else:
        sales = int(sales)
    return sales

def yesterday_time():
    # 获取昨天的时间
    import datetime
    now_time = datetime.datetime.now()
    yes_time = now_time + datetime.timedelta(days=-1)
    yes_time_nyr = yes_time.strftime('%Y-%m-%d %H:%M:%S')
    # print(yes_time_nyr)
    return str(yes_time_nyr)

async def download_imgs(platform, ims, skuid=None):
    """  图片下载  """
    if ims == []:
        return
    for img in ims:
        if 'yf-oversea-bj.oss-us-west-1.aliyuncs.com' in img:
            raise AssertionError(f'图片格式异常 img_url:{img}')
    task_list = [json.dumps({"platform": platform, "pic_name": f"sku/{gen_md5(im)}.webp", "img_url": im, 'skuid':skuid}) for
                 im in
                 ims]

    works_task_item = {

        "taskData": task_list,
        "taskName": 'oversea-goods-imgs',
        "submitter":f'{platform}-goods-imgs',
        "forceTask": False,
        "globalFilter": True

    }

    ret = await push_task2(works_task_item)
    # print(f'任务提交结果：{ret}')

# @retry(stop_max_attempt_number=3, wait_fixed=1000)
async def push_task2(data):
    retry_times = 0
    additional_data = None
    while(retry_times < 3):
        try:
            url = DM_SCHEDULER_URL + 'addTask'
            connector = aiohttp.TCPConnector(limit=5, verify_ssl=False)  # 并发数量
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, json=data) as additional_response:
                    additional_data = await additional_response.json()
                    await asyncio.sleep(1)
                    additional_response.close()
                await session.close()
            break
        except:
            retry_times = retry_times + 1
    return additional_data

def get_oss_imgs(platform, imgs):
    for img in imgs:
        if 'yf-oversea-bj.oss-us-west-1.aliyuncs.com' in img:
            raise AssertionError(f'图片格式异常 img_url:{img}')
    oss_imgs = [f"https://creator-yf-oversea-bj.oss-us-west-1.aliyuncs.com/sku/{platform}/" + gen_md5(img) + ".webp" for img in imgs]
    return oss_imgs

def filter_html_label(text):
    """
    处理字符串
    """
    if text == None:
        return ''
    text = str(text)
    text = ''.join([i for i in text if i.isprintable()])
    if re.search(r'[0-9a-z]', text.lower()) == None:
        try:
            text = text.encode('raw_unicode_escape').decode()
        except:
            pass
    text = html.unescape(text)
    # text = text.encode().decode('unicode_escape')
    filter_char_list = [
        u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000', u'\u200a', u'\u200b', u'\u2028', u'\u2029', u'\u202f',
        u'\u205f',
        u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F', '\t', '\n', '\r', '\f', '\v',
    ]
    for f_char in filter_char_list:
        text = text.replace(f_char, ' ')
    text = re.sub(r' +',' ',text)
    text = text.strip()
    return text


def get_item(response):
    """
    解析商品详情页信息
    """
    key_label = ["name", "description", "image", "offers", "brand", "mpn", "sku"]
    all_results = re.findall('<script .*?type="application/ld\+json".*?>(.*?)</script>', response.text, re.S)
    for _result in all_results:
        try:
            a_result = json.loads(_result)
            inter_ = set(a_result.keys()).intersection(set(key_label))
            if len(inter_) > 4:
                results = a_result
                break
        except:
            pass

    if isinstance(results.get("offers"), list):
        skuid = results.get("sku") if results.get("sku") else results["offers"][0]["sku"]
        prices = [float(i["price"]) for i in results["offers"]]
        cur_price = min(prices)
        ori_price = max(prices)
    else:
        skuid = results.get("sku")
        cur_price = float(results["offers"]["price"])
        ori_price = float(results["offers"]["price"])

    itemid = skuid
    brand = results["brand"]["name"] if isinstance(results.get("brand"), dict) else results.get("brand")
    description = results["description"] if isinstance(results["description"], list) else [results["description"]]
    title = results.get("name")
    imgs = results["image"] if isinstance(results["image"], list) else [results["image"]]

    if isinstance(results["offers"], dict):
        price_unit = results["offers"]["priceCurrency"]
    elif isinstance(results["offers"], list):
        price_unit = results["offers"][0]["priceCurrency"]
    if price_unit != "USD":
        print("price_unit:", price_unit)
        raise ValueError("price_unit  not is $   please retry requests may is env question")

    specs = []
    item = {
        "itemid": itemid,
        "skuid": skuid,
        "title": title,
        "description": description,
        "price": cur_price,
        "orig_price": ori_price,
        "orig_imgs": imgs,
        "brand_name": brand,
        "specs": specs,
    }
    return item