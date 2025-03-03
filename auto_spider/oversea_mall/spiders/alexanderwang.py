# -*- coding: utf-8 -*-
# @Time : 2024-04-30 17:24
# @Author : Mo

import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from scrapy import Selector
import warnings
import traceback
from datetime import datetime
from urllib.parse import urljoin, urlencode, urlparse
import json
import re
import price_parser
import scrapy
from dmscrapy import defaults
from dmscrapy.items import PostData
from dmscrapy.dm_spider import DmSpider
from utils.tools import get_now_datetime, download_imgs, gen_md5, get_oss_imgs, filter_html_label
from auto_parse.get_parse_info import get_auto_parse_info
from auto_parse.tools import get_info_from_auto_parse
from oversea_mall.auto_parse_class import AutoParse
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class GoodsAllListSpider(DmSpider, AutoParse):
    name = 'alexanderwang:goods_all_list'
    platform = "alexanderwang"
    task_id = 'alexanderwang'
    sch_task = 'alexanderwang-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        # 'DOWNLOAD_HANDLERS': {
        #     'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
        #     'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        # },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 0,
        'DOWNLOAD_TIMEOUT': 10,
        "LOG_LEVEL": "INFO",
        "EXIT_ENABLED": True,
        'LOG_FILE': log_file_path,
        'LOG_STDOUT': False,
        'REDIRECT_ENABLED': False
    }

    headers = {}
    cookies = {}
    proxies = {}
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        urls = [
            'https://www.alexanderwang.com/us-en/women-newarrivals',
            'https://www.alexanderwang.com/us-en/women-shirts',
            'https://www.alexanderwang.com/us-en/women-tshirts',
            'https://www.alexanderwang.com/us-en/women-sweaters',
            'https://www.alexanderwang.com/us-en/women-sweatshirts',
            'https://www.alexanderwang.com/us-en/women-pants',
            'https://www.alexanderwang.com/us-en/women-denim',
            'https://www.alexanderwang.com/us-en/women-sweatpants',
            'https://www.alexanderwang.com/us-en/women-shorts',
            'https://www.alexanderwang.com/us-en/women-skirts',
            'https://www.alexanderwang.com/us-en/women-jackets',
            'https://www.alexanderwang.com/us-en/women-dresses',
            'https://www.alexanderwang.com/us-en/women-outerwear',
            'https://www.alexanderwang.com/us-en/women-bags',
            'https://www.alexanderwang.com/us-en/women-accessories',
            'https://www.alexanderwang.com/us-en/women-shoes',
            'https://www.alexanderwang.com/us-en/women-children',
            'https://www.alexanderwang.com/us-en/women-unisex',
            'https://www.alexanderwang.com/us-en/men-tops',
            'https://www.alexanderwang.com/us-en/men-sweaters',
            'https://www.alexanderwang.com/us-en/men-bottoms',
            'https://www.alexanderwang.com/us-en/men-jackets',
            'https://www.alexanderwang.com/us-en/men-shoes',
            'https://www.alexanderwang.com/us-en/men-accessories',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': 1}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        meta = response.meta
        page = meta['page']
        meta['page'] = page
        cgid = response.url.split('/')[-1]
        meta['cgid'] = cgid
        params = {
            "cgid": cgid,
            "start": str(12*page),
            "format": "json"
        }
        url = "https://www.alexanderwang.com/us-en/search?" + urlencode(params)

        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta=meta
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        cgid = meta['cgid']
        meta['cgid'] = cgid

        products = response.json()["search"]["grid"]["products"]
        for product in products:
            masterProductAbsoluteUrl = product["masterProductAbsoluteUrl"]
            yield scrapy.Request(
                url=masterProductAbsoluteUrl,
                callback=self.parse_detail,
                meta=meta
            )

        if len(products):
            page += 1
            params = {
                "cgid": cgid,
                "start": str(12 * page),
                "format": "json"
            }
            url = "https://www.alexanderwang.com/us-en/search?" + urlencode(params)
            meta['page'] = page
            meta['cgid'] = cgid
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta=meta
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        meta = response.meta
        pattern = r'}\)\(({.*?)\);'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        itemid = json_data["product"]["product"]["id"]
        skuid = json_data["product"]["product"]["id"]
        title = json_data["product"]["product"]["productName"]
        brand = json_data["product"]["product"]["brand"]
        if brand == None:
            brand = 'alexanderwang'
        breadlist = meta["cgid"]

        cur_price = float(json_data["product"]["product"]["price"]["sales"]["value"])
        ori_price = float(json_data["product"]["product"]["price"]["sales"]["value"])
        oversold_all = not json_data["product"]["product"]["available"]

        description = []
        description_data = json_data["product"]["product"]["longDescription"]
        pattern = r'>(.*?)<'

        if description_data != None:
            clean_text = re.findall(pattern, description_data)
            if clean_text != [] and clean_text != ['']:
                for clean in clean_text:
                    if clean.replace(' ', '').replace('\r', '') != '':
                        description.append(clean)
            else:
                description = [description_data]
        else:
            description = []

        imgs = []
        images = json_data["product"]["product"]["highResolutionImages"]["hi-res"]
        for image in images:
            imgs.append(image["absoluteUrl"])

        specs = []
        variants = json_data["product"]["product"]["variationAttributes"][0]["values"]
        for variant in variants:
            spec = {
                'spec': variant["value"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not variant["selectable"]
            }
            specs.append(spec)

        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": str(itemid),
            "skuid": str(skuid),
            "title": title,
            "price": cur_price,
            "orig_price": ori_price,
            "price_unit": "$",
            "prices": {"US": {"p": cur_price, "o": ori_price, 'u': "$"}},
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": response.url,
            "brand_name": brand,
            "category_info": breadlist,
            "specs": specs,
            "description": description,
            "insert_time": get_now_datetime(),
            "online": True,
            "oversold": oversold_all,
        }

        # print(item)
        logger.info(item)

        data = PostData()
        data['dataRows'] = [item]
        data['name'] = 'goods_base'
        data[defaults.DM_SCHEDULER_TASK_ID] = response.meta.get(defaults.DM_SCHEDULER_TASK_ID)
        data[defaults.DM_SCHEDULER_FORCE_TASK] = response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)
        yield data


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl alexanderwang:goods_all_list'.split(' '))
