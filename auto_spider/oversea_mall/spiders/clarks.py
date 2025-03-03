# -*- coding: utf-8 -*-
# @Time : 2024-04-08 11:00
# @Author : Mo

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import warnings
import traceback
from datetime import datetime
from urllib.parse import urljoin
import json
import re
import price_parser
import scrapy
from dmscrapy import defaults
from dmscrapy.items import PostData
from dmscrapy.dm_spider import DmSpider
from utils.tools import get_now_datetime, download_imgs, gen_md5, get_oss_imgs
from auto_parse.get_parse_info import get_auto_parse_info
from auto_parse.tools import get_info_from_auto_parse
from oversea_mall.auto_parse_class import AutoParse

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class GoodsAllListSpider(DmSpider, AutoParse):
    name = 'clarks:goods_all_list'
    platform = "clarks"
    task_id = 'clarks'
    sch_task = 'clarks-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
            'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        },
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
            # 'https://www.clarks.com/en-us/womens-all-styles/w_allstyles_us-c',
            # 'https://www.clarks.com/en-us/mens-all-styles/m_allstyles_us-c',
            'https://www.clarks.com/en-us/all-kids-styles/k_allstyles_us-c',
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
        page = 1
        url = "https://kij46symwd-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key=14be9e2da22ce62ef749138c685e623b&x-algolia-application-id=KIJ46SYMWD"
        data = {
            "requests": [
                {
                    "indexName": "prod_product_us",
                    "params": f"facets=%5B%22&page={page}"
                }
            ]
        }
        data = json.dumps(data, separators=(',', ':'))

        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            body=data,
            method="POST",
            meta={'page': page}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        json_data = response.json()
        page = response.meta['page']
        hits = json_data['results'][0]['hits']
        for hit in hits:
            url = 'https://www.clarks.com/en-us/' + hit['slug.en-US'] + '/' + hit['objectID'] + '-p'
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        if len(hits):
            page += 1
            url = "https://kij46symwd-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key=14be9e2da22ce62ef749138c685e623b&x-algolia-application-id=KIJ46SYMWD"
            data = {
                "requests": [
                    {
                        "indexName": "prod_product_us",
                        "params": f"facets=%5B%22&page={page}"
                    }
                ]
            }
            data = json.dumps(data, separators=(',', ':'))

            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                body=data,
                method="POST",
                meta={'page': page},
            )

    async def parse_detail(self, response, **kwargs):
        div_list = response.xpath('//*[@id="pdp-sticky-container"]/section/div[2]/div/div/div')
        for div in div_list:
            url = 'https://www.clarks.com' + div.xpath('./div/a/@href').extract()[0]
            yield scrapy.Request(
                url=url,
                callback=self.parse_item_detail,
                dont_filter=True
            )

    @AutoParse.check_parse_info
    async def parse_item_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        global breadlist, cur_price, ori_price
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["props"]["pageProps"]["product"]["key"]
        skuid = json_data["props"]["pageProps"]["product"]["key"]
        title = json_data["props"]["pageProps"]["product"]["metaTitle"]

        description = [json_data["props"]["pageProps"]["product"]["description"]]
        features = json_data["props"]["pageProps"]["product"]["features"]
        pattern = r'>(.*?)<'
        try:
            clean_text = re.findall(pattern, features[0].replace('\n', ''))
            for clean in clean_text:
                if clean.replace(' ', '') != '':
                    description.append(clean)
        except:
            pass

        categoriesPath = json_data["props"]["pageProps"]["product"]["categoriesPath"]
        for categoryPath in categoriesPath:
            if categoryPath == categoriesPath[0]:
                breadlist = categoryPath["name"]
            else:
                breadlist += ' / ' + categoryPath["name"]
        brand = json_data["props"]["pageProps"]["product"]["brand"]
        oversold_all = True
        imgs = json_data["props"]["pageProps"]["product"]["imageUrls"]
        specs = []

        variants = json_data["props"]["pageProps"]["product"]["variants"]
        for variant in variants:
            availableQuantity = variant["stock"]["availableQuantity"]
            if availableQuantity:
                oversold = False
            else:
                oversold = True
            if oversold == False:
                oversold_all = False
            cur_price = float(str(variant["price"][0]["actualPrice"]["centAmount"])[:-2] + '.' + str(
                variant["price"][0]["actualPrice"]["centAmount"])[-2:])
            try:
                ori_price = float(str(variant["price"][0]["wasPrice"]["centAmount"])[:-2] + '.' + str(
                    variant["price"][0]["wasPrice"]["centAmount"])[-2:])
            except:
                ori_price = cur_price
            spec = {
                'spec': variant["size"] + ' / ' + variant['fitLabel'],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": oversold
            }

            specs.append(spec)

        # oss_imgs = imgs
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
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


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl clarks:goods_all_list'.split(' '))
