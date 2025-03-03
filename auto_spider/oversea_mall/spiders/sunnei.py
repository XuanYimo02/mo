# -*- coding: utf-8 -*-
# @Time : 2024-04-26 15:37
# @Author : Mo

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
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
    name = 'sunnei:goods_all_list'
    platform = "sunnei"
    task_id = 'sunnei'
    sch_task = 'sunnei-task'
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
            'https://sunnei.it/collections/ss24-all-man',
            'https://sunnei.it/collections/ss24-all-woman'
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        pattern = r'webPixelsManagerAPI.publish\("collection_viewed", (.*?)\);'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        productVariants = json_data["collection"]["productVariants"]
        for productVariant in productVariants:
            url = response.url + productVariant["product"]["url"]
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script type="application/json" data-product-json>      (.*?)    </script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["id"]
        skuid = json_data["id"]
        title = json_data["title"]
        brand = json_data["vendor"]
        breadlist = json_data["type"]
        cur_price = float(str(json_data["price"])[:-2] + '.' + str(json_data["price"])[-2:])
        if json_data["compare_at_price"] == None:
            ori_price = cur_price
        else:
            ori_price = float(str(json_data["compare_at_price"])[:-2] + '.' + str(
                json_data["compare_at_price"])[-2:])
        oversold_all = not json_data["available"]

        description = []
        description_data = json_data["description"].replace('\n', '')
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
        images = json_data["images"]
        for image in images:
            imgs.append("https:" + image)

        specs = []
        variants = json_data["variants"]
        for variant in variants:
            price = float(str(variant["price"])[:-2] + '.' + str(variant["price"])[-2:])
            if variant["compare_at_price"] == None:
                origPrice = price
            else:
                origPrice = float(str(variant["compare_at_price"])[:-2] + '.' + str(variant["compare_at_price"])[-2:])
            spec = {
                'spec': variant["title"],
                "price": price,
                "origPrice": origPrice,
                "priceUnit": "$",
                "oversold": not variant["available"]
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

    execute('scrapy crawl sunnei:goods_all_list'.split(' '))
