# -*- coding: utf-8 -*-
# @Time : 2024-06-05 12:01
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
    name = 'stuartweitzman:goods_all_list'
    platform = "stuartweitzman"
    task_id = 'stuartweitzman'
    sch_task = 'stuartweitzman-task'
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
            'https://www.stuartweitzman.com/shop/new-arrivals/all-new-arrivals',
            'https://www.stuartweitzman.com/shop/collections/sw-icons',
            'https://www.stuartweitzman.com/shop/shoes/shop-all',
            'https://www.stuartweitzman.com/shop/sandals/shop-all',
            'https://www.stuartweitzman.com/shop/boots-booties/shop-all',
            'https://www.stuartweitzman.com/shop/handbags/shop-all',
            'https://www.stuartweitzman.com/shop/collections/sw-weddings',
            'https://www.stuartweitzman.com/shop/mens/shop-all'
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
        gid = response.url.split('https://www.stuartweitzman.com/shop/')[-1]
        params = {
            "page": "1",
            "__v__": "tVrebhBtOq-U-ZRLMBrpt"
        }
        url = "https://www.stuartweitzman.com/api/get-shop/" + gid + '?' + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': 1, 'gid': gid}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        gid = meta['gid']
        products = response.json()["pageData"]["products"]
        for product in products:
            url = 'https://www.stuartweitzman.com' + product["defaultColor"]["url"]
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        # print(len(products), response)
        if len(products):
            page += 1
            meta['page'] = page
            meta['gid'] = gid
            params = {
                "page": page,
                "__v__": "tVrebhBtOq-U-ZRLMBrpt"
            }
            url = "https://www.stuartweitzman.com/api/get-shop/" + gid + '?' + urlencode(params)

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
        global breadlist
        pattern = r'type="application/json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))["props"]["pageProps"]["pageData"]

        itemid = json_data["selectedVariantGroupData"]["id"]
        skuid = json_data["selectedVariantGroupData"]["id"]
        title = json_data["name"]
        brand = 'stuartweitzman'
        item_category = json_data["item_category"]
        for category in item_category:
            if category == item_category[0]:
                breadlist = category
            else:
                breadlist += ' / ' + category
        cur_price = json_data["selectedVariantGroupData"]["pricingInfo"][0]["sales"]["value"]
        try:
            ori_price = json_data["selectedVariantGroupData"]["pricingInfo"][0]["list"]["value"]
        except:
            ori_price = cur_price

        description = [json_data["shortDescription"]]

        imgs = []
        images = json_data["variationGroup"][0]["imageGroups"][1]["images"]
        for image in images:
            imgs.append(image["src"])

        oversold_all = True
        color = json_data["variant"][0]["customAttributes"]["c_colorVal"]
        specs = []
        try:
            variants = json_data["selectedVariantGroupData"]["variationAttributes"][1]["values"]
            for variant in variants:
                if variant["orderable"] == True:
                    oversold_all = False
                spec = {
                    'spec': color + ' / ' + variant["name"],
                    "price": cur_price,
                    "origPrice": ori_price,
                    "priceUnit": "$",
                    "oversold": not variant["orderable"]
                }
                specs.append(spec)
        except:
            oversold_all = not json_data["variant"][0]["customAttributes"]["c_availableForInStorePickup"]
            spec = {
                'spec': color,
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not json_data["variant"][0]["customAttributes"]["c_availableForInStorePickup"]
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

    execute('scrapy crawl stuartweitzman:goods_all_list'.split(' '))
