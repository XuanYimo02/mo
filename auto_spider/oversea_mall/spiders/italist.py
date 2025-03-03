# -*- coding: utf-8 -*-
# @Time : 2024-03-22 12:19
# @Author : Mo

import logging
import os
import random
import sys

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
    name = 'italist:goods_all_list'
    platform = "italist"
    task_id = 'italist'
    sch_task = 'italist-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "ITEM_PIPELINES": {
            'dmscrapy.pipelines.DmDataDisPipeline2': 100,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        # 'DOWNLOAD_HANDLERS': {
        #     'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
        #     'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        # },
        "EXTENSIONS": {
            'dmscrapy.extensions.DmSpiderSmartIdleClosedExensions': 500
        },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 0,
        'DOWNLOAD_TIMEOUT': 30,
        "LOG_LEVEL": "INFO",
        "EXIT_ENABLED": True,
        'LOG_FILE': log_file_path,
        'LOG_STDOUT': False,
        'REDIRECT_ENABLED': False
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "italistsession-v2": "s%3A53f12252-2637-4126-a816-2752447152ad.SXlI2mdp5my0ph3p65zMa9mqSDLhd6y%2FrYQhNCqLEJA"
    }
    proxies = {}
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        urls = [
            'https://www.italist.com/us/men/',
            'https://www.italist.com/us/women/',
            'https://www.italist.com/us/kids/'
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                dont_filter=False,
                callback=self.parse_home,
                headers=self.headers,
                cookies=self.cookies
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """

        pid = response.url.split('/')[-2]
        url = f'https://www.italist.com/api/search_products/{pid}?skip=0'

        yield scrapy.Request(
            url=url,
            dont_filter=False,
            callback=self.parse_list,
            headers=self.headers,
            cookies=self.cookies,
            meta={
                'skip': 0
            }
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        data_json = response.json()
        products = data_json["products"]
        for product in products:
            url = 'https://www.italist.com/us' + product['url'] + '/'
            yield scrapy.Request(
                url=url,
                dont_filter=False,
                callback=self.parse_detail,
                headers=self.headers,
                cookies=self.cookies
            )
        try:
            if products:
                skip = meta.get('skip')
                skip += 60
                meta['skip'] = skip
                next_url = response.url.split('skip=')[0] + 'skip=' + str(skip)
                yield scrapy.Request(
                    url=next_url,
                    callback=self.parse_list,
                    meta=meta,
                    headers=self.headers,
                    cookies=self.cookies
                )
        except:
            pass

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        data_start = response.text
        result = re.search(pattern, data_start)
        json_data_1 = json.loads(result.group(1))

        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        data_start = response.text
        result = re.search(pattern, data_start)
        json_data_2 = json.loads(result.group(1))

        itemid = json_data_2["productGroupID"]
        skuid = json_data_2["productGroupID"]
        title = json_data_2["name"]
        brand = json_data_1["props"]["pageProps"]["productDetails"]["product"]["brand"]["name"]
        cur_price = float(json_data_2["hasVariant"][0]["offers"][0]["price"])
        ori = str(json_data_1["props"]["pageProps"]["productDetails"]["product"]["price"]["baseBeforeTax"])
        ori_price = float(f'{ori[:-2]}.{ori[-2:]}')
        # ori_price = response.xpath(
        #     '//*[@id="root"]/div[2]/div[2]/div[3]/div/div/div/div[1]/div/div[2]/div/div/div[1]/span[1]/text()').extract()[0]
        # '//*[@id="root"]/div[2]/div[1]/div[3]/div/div/div/div[1]/div/div[2]/div/div/div[1]/div[1]/text()'
        # ori_price = float(re.findall(r'USD (.*)', ori_price)[0])
        categoryPaths = json_data_1["props"]["pageProps"]["productDetails"]["product"]["categoryPath"]
        breadlist = ''
        for categoryPath in categoryPaths[::-1]:
            breadlist += categoryPath['name'] + ' / '
        breadlist += brand
        imgs = []
        specs = []
        images = json_data_1["props"]["pageProps"]["productDetails"]["product"]["images"]
        for image in images:
            imgs.append(image['zoom'])

        # oss_imgs = imgs
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)

        size_list = json_data_1["props"]["pageProps"]["productDetails"]["product"]["sizesList"]
        for sz in size_list:
            size = sz['size']
            if sz['numberAvailable']:
                oversold = False
            else:
                oversold = True

            spec = {
                "spec": size,
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": oversold,
            }
            specs.append(spec)

        description = []
        description_data = json_data_1["props"]["pageProps"]["productDetails"]["product"]["description"]

        clean_text = description_data.replace('\n', '').split('<br>')
        if clean_text != [] and clean_text != ['']:
            for clean in clean_text:
                if clean.replace(' ', '').replace('\r', '') != '':
                    description.append(clean)
        else:
            description = [description_data]

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
            "oversold": False,
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

    execute('scrapy crawl italist:goods_all_list'.split(' '))
