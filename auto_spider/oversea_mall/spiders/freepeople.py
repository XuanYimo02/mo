# -*- coding: utf-8 -*-
# @Time : 2024-05-30 15:02
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
    num = 0
    name = 'freepeople:goods_all_list'
    platform = "freepeople"
    task_id = 'freepeople'
    sch_task = 'freepeople-task'
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
            'https://us.burberry.com/womens-clothing/',
            'https://us.burberry.com/l/womens-new-arrivals-new-in/',
            'https://us.burberry.com/womens-bags/',
            'https://us.burberry.com/womens-shoes/',
            'https://us.burberry.com/l/womens-accessories/',
            'https://us.burberry.com/l/scarves/',
            'https://us.burberry.com/l/womens-gifts/',
            'https://us.burberry.com/l/mens-new-arrivals-new-in/',
            'https://us.burberry.com/mens-clothing/',
            'https://us.burberry.com/mens-bags/',
            'https://us.burberry.com/mens-shoes/',
            'https://us.burberry.com/l/mens-accessories/',
            'https://us.burberry.com/l/scarves/',
            'https://us.burberry.com/l/mens-gifts/',
            'https://us.burberry.com/l/childrens-new-arrivals/',
            'https://us.burberry.com/l/newborn-clothes/',
            'https://us.burberry.com/baby/',
            'https://us.burberry.com/girl/',
            'https://us.burberry.com/boy/',
            'https://us.burberry.com/childrens-accessories/',
            'https://us.burberry.com/childrens-gifts/',
            'https://us.burberry.com/l/womens-trench-coats/',
            'https://us.burberry.com/l/mens-trench-coats/',
            'https://us.burberry.com/womens-bags/',
            'https://us.burberry.com/mens-bags/',
            'https://us.burberry.com/l/womens-gifts/',
            'https://us.burberry.com/l/mens-gifts/',
            'https://us.burberry.com/childrens-gifts/',
            'https://us.burberry.com/l/womens-accessories/',
            'https://us.burberry.com/l/beauty/make-up/',
            'https://us.burberry.com/l/beauty/fragrances/',
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
        pattern = r'window.__PRELOADED_STATE__ =(.*?});'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        location = ''
        catalogBreadcrumbs = json_data["pages"]["entities"][response.url.split('https://us.burberry.com')[-1]]["components"]["catalogBreadcrumbs"]
        for catalogBreadcrumb in catalogBreadcrumbs:
            location += '/' + catalogBreadcrumb["id"]

        params = {
            "location": location,
            "offset": "0",
            "limit": "20",
            "isNewProductCard": "false",
            "language": "en",
            "country": "US"
        }
        url = "https://us.burberry.com/web-api/pages/products?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': 0, 'location': location}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        location = meta['location']

        items = response.json()["data"]["products"][0]["items"]
        for item in items:
            try:
                url = 'https://us.burberry.com' + item["url"]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers
                )
            except:
                pass

        # print(location, page, len(items))
        if len(items):
            page += 20
            meta['page'] = page
            meta['location'] = location
            params = {
                "location": location,
                "offset": page,
                "limit": "20",
                "isNewProductCard": "false",
                "language": "en",
                "country": "US"
            }
            url = "https://us.burberry.com/web-api/pages/products?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
                meta=meta
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'window.__PRELOADED_STATE__ = (.*?});'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        currentUrl = json_data["pages"]["currentUrl"]
        itemid = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["id"]
        skuid = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["id"]
        title = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["name"]
        description = [json_data["pages"]["entities"][currentUrl]["properties"]["product"]["description"]]
        color = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["color"]
        cur_price = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["price"]["current"]["value"]
        ori_price = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["price"]["old"]
        if ori_price == None:
            ori_price = cur_price
        brand = 'Burberry'
        breadlist = ''
        catalogBreadcrumbs = json_data["pages"]["entities"][currentUrl]["components"]["catalogBreadcrumbs"]
        for catalogBreadcrumb in catalogBreadcrumbs:
            if catalogBreadcrumb == catalogBreadcrumbs[0]:
                breadlist = catalogBreadcrumb["title"]
            else:
                breadlist += ' / ' + catalogBreadcrumb["title"]

        specs = []
        oversold_all = True
        variants = json_data["pages"]["entities"][currentUrl]["properties"]["product"]["sizes"]
        for variant in variants:
            if variant["isInStock"]:
                oversold_all = False
            spec = {
                'spec': color + ' / ' + variant["label"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not variant["isInStock"]
            }
            specs.append(spec)

        imgs = []
        images = json_data["pages"]["entities"][currentUrl]["components"]["gallery"]["items"]
        for image in images:
            try:
                img = image["image"]["imageFallback"]
                imgs.append(img)
            except:
                pass

        oss_imgs = get_oss_imgs(self.platform, imgs)
        # await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": itemid,
            "skuid": skuid,
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

    async def parse_detail_js(self, response, **kwargs):
        pass

if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl freepeople:goods_all_list'.split(' '))
