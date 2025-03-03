# -*- coding: utf-8 -*-
from mall.items import SpiderItem
from utils.tools import get_now_datetime


def gen_closed_shop_item(platform, shop_id):
    item = {
        "platform": platform,
        "shopid": shop_id,
        "isOpen": False,
        "insert_time": get_now_datetime()
    }
    closed_shop_item = SpiderItem()
    closed_shop_item['name'] = 'shop_base'
    closed_shop_item['data_rows'] = [item]
    return closed_shop_item
