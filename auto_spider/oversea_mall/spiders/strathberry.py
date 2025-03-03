# -*- coding: utf-8 -*-
# @Time : 2024-04-03 11:20
# @Author : Mo

import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import warnings
import traceback
from datetime import datetime
from urllib.parse import urljoin, urlencode
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
    name = 'strathberry:goods_all_list'
    platform = "strathberry"
    task_id = 'strathberry'
    sch_task = 'strathberry-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        # 'DOWNLOAD_HANDLERS': {
            # 'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
            # 'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
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
            # 'https://us.strathberry.com/collections/gifts',
            # 'https://us.strathberry.com/collections/cashmere',
            # 'https://us.strathberry.com/collections/jewelry',
            # 'https://us.strathberry.com/collections/accessories',
            'https://us.strathberry.com/collections/the-strathberry-designer-collection',
            # 'https://us.strathberry.com/collections/bestsellers',
            # 'https://us.strathberry.com/collections/new-arrivals',
            # 'https://us.strathberry.com/collections/sale',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_home,
            )

    async def parse_home(self, response):
        """
        爬虫首页抓取
        """
        page = 1
        url = 'https://vr0txpe36h-2.algolia.net/1/indexes/*/queries?x-algolia-api-key=fa1cb50aae30af98fef9dc9948d76f37&x-algolia-application-id=VR0TXPE36H'
        data = {
            "requests": [
                {
                    "indexName": "shopify_us_products",
                    "params": f"facets=%5B%22&page={page}"
                }
            ],
        }

        data = json.dumps(data, separators=(',', ':'))

        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            body=data,
            method="POST",
            meta={'page': page},
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        retry_times_1 = 0
        json_data = response.json()
        page = response.meta['page']
        hits = json_data['results'][0]['hits']
        for hit in hits:
            url = 'https://us.strathberry.com/products/' + hit['handle']
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={'retry_times_1': retry_times_1},
            )

        if len(hits):
            page += 1
            url = 'https://vr0txpe36h-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key=fa1cb50aae30af98fef9dc9948d76f37&x-algolia-application-id=VR0TXPE36H'
            data = {
                "requests": [
                    {
                        "indexName": "shopify_us_products",
                        "params": f"facets=%5B%22&page={page}"
                    }
                ],
            }
            data = json.dumps(data, separators=(',', ':'))

            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                body=data,
                method="POST",
                meta={'page': page}
            )

    async def parse_detail(self, response, **kwargs):
        retry_times_2 = 0
        retry_times_1 = response.meta['retry_times_1']
        global specs_data
        pattern = r'productHandle", "colourVariantsPromise", (.*?)\)</script>'
        data_start = response.text.replace('\n', '')
        try:
            result = re.search(pattern, data_start)
            specs_data = json.loads(result.group(1))
            for specs in specs_data:
                if "us" in specs["onlineStoreUrl"]:
                    onlineStoreUrl = specs["onlineStoreUrl"].split('checkout.')[0] + \
                                     specs["onlineStoreUrl"].split('checkout.')[1]
                else:
                    onlineStoreUrl = specs["onlineStoreUrl"].split('checkout.')[0] + 'us.' +\
                                     specs["onlineStoreUrl"].split('checkout.')[1]
                yield scrapy.Request(
                    url=onlineStoreUrl,
                    callback=self.parse_item_list,
                    dont_filter=True,
                    meta={'retry_times_2': retry_times_2}
                )
        except:
            if retry_times_1 < 5:
                retry_times_1 += 1
                yield scrapy.Request(
                    url=response.url,
                    callback=self.parse_detail,
                    dont_filter=True,
                    meta={'retry_times_1': retry_times_1}
                )
            else:
                logger.error(f'{response.url}解析有误')
            return

    @AutoParse.check_parse_info
    async def parse_item_list(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        retry_times_2 = response.meta['retry_times_2']
        global breadlist, json_data, specs_data
        pattern = r'state":(.*?),"future":'
        data_start = response.text.replace('\n', '')

        try:
            result = re.search(pattern, data_start)
            json_data = json.loads(result.group(1))
        except:
            if retry_times_2 < 5:
                retry_times_2 += 1
                yield scrapy.Request(
                    url=response.url,
                    callback=self.parse_item_list,
                    dont_filter=True,
                    meta={'retry_times_2': retry_times_2}
                )
            else:
                logger.error(f'{response.url}解析有误')
            return

        pattern = r'productHandle", "colourVariantsPromise", (.*?)\)</script>'
        data_start = response.text.replace('\n', '')
        try:
            result = re.search(pattern, data_start)
            specs_data = json.loads(result.group(1))
        except:
            if retry_times_2 < 5:
                retry_times_2 += 1
                yield scrapy.Request(
                    url=response.url,
                    callback=self.parse_item_list,
                    dont_filter=True,
                    meta={'retry_times_2': retry_times_2}
                )
            else:
                logger.error(f'{response.url}解析有误')
            return

        bread_list = response.xpath('//*[@id="mainContent"]/ul/li')
        for bread in bread_list[1:]:
            if bread == bread_list[1]:
                breadlist = bread.xpath('./text()').extract()[0]
            else:
                breadlist += ' / ' + bread.xpath('./text()').extract()[0]
        itemid = json_data["loaderData"]["routes/products/$productHandle"]["product"]["id"].split('/')[-1]
        skuid = json_data["loaderData"]["routes/products/$productHandle"]["product"]["id"].split('/')[-1]
        title = json_data["loaderData"]["routes/products/$productHandle"]["product"]["title"]
        ori_price = \
        json_data["loaderData"]["routes/products/$productHandle"]["product"]["variants"]["edges"][0]["node"][
            "compareAtPrice"]
        cur_price = \
        json_data["loaderData"]["routes/products/$productHandle"]["product"]["variants"]["edges"][0]["node"]["price"][
            "amount"]
        if ori_price:
            ori_price = \
            json_data["loaderData"]["routes/products/$productHandle"]["product"]["variants"]["edges"][0]["node"][
                "compareAtPrice"]['amount']
        else:
            ori_price = cur_price
        oversold_all = True

        specs = []
        imgs = []
        div_list = response.xpath('//*[@id="mainContent"]/section[1]/div/div[2]/div')
        for div in div_list:
            try:
                pic_url = div.xpath('./img/@src').extract()[0]
                imgs.append(pic_url)
            except:
                pass
        for specs_li in specs_data:
            if specs_li['id'] == json_data["loaderData"]["routes/products/$productHandle"]["product"]["id"]:
                if specs_li["variants"]["edges"][0]["node"]["availableForSale"]:
                    oversold_all = False
                # nodes = specs_li["media"]["nodes"]
                # for node in nodes:
                #     img_url = node["image"]["url"]
                #     imgs.append(img_url)
                origPrice = specs_li["variants"]["edges"][0]["node"]["compareAtPrice"]
                if origPrice:
                    origPrice = specs_li["variants"]["edges"][0]["node"]["compareAtPrice"]["amount"]
                else:
                    origPrice = specs_li["variants"]["edges"][0]["node"]["price"]["amount"]
                spec = {
                    "spec": specs_li['swatch'],
                    "price": float(specs_li["variants"]["edges"][0]["node"]["price"]["amount"]),
                    "origPrice": float(origPrice),
                    "priceUnit": "$",
                    "oversold": not specs_li["variants"]["edges"][0]["node"]["availableForSale"],
                }
                specs.append(spec)

        description = []
        descriptionHtml = json_data["loaderData"]["routes/products/$productHandle"]["product"]["descriptionHtml"]
        pattern = r'>(.*?)<'

        clean_text = re.findall(pattern, descriptionHtml.replace('\n', ''))
        if clean_text != [] and clean_text != ['']:
            for clean in clean_text:
                if clean.replace(' ', '').replace('\r', '') != '':
                    description.append(clean)
        else:
            description = [descriptionHtml]

        # oss_imgs = imgs
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": itemid,
            "skuid": skuid,
            "title": title,
            "price": float(cur_price),
            "orig_price": float(ori_price),
            "price_unit": "$",
            "prices": {"US": {"p": float(cur_price), "o": float(ori_price), 'u': "$"}},
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": response.url,
            "brand_name": self.platform,
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

    execute('scrapy crawl strathberry:goods_all_list'.split(' '))
