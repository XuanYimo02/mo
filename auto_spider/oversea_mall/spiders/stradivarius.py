# -*- coding: utf-8 -*-
# @Time : 2024-06-12 10:15
# @Author : Mo

import logging
import os
import sys

import requests

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
    name = 'stradivarius:goods_all_list'
    platform = "stradivarius"
    task_id = 'stradivarius'
    sch_task = 'stradivarius-task'
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

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "priority": "u=1, i",
        "referer": "https://www.stradivarius.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    cookies = {}
    current_proxy_ip = 'http://astoip451-country-US:ef1772-d18d43-e0da31-41f501-ed5f24@209.205.219.18:9001'
    current_proxies = {
        'http': current_proxy_ip,
        'https': current_proxy_ip,
    }
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        cgids = [
            '1020620921',
            '1020428824',
            '1020047059',
            '1020206147',
            '1020047051',
            '1020598297',
            '1020355018',
            '1020218001',
            '1020047067',
            '1020206021',
            '1020047036',
            '1020507059',
            '1020047030',
            '1020424302',
            '1020132510',
            '1020047045',
            '1020508065',
            '1020433925',
            '1020283521',
            '1020623411',
            '1020167001',
            '1020508562',
            '1020610803',
            '1020347013',
            '1020343508',
            '1020330394',
            '1020273100',
            '1020330483',
        ]
        for cgid in cgids:
            url = f'https://www.stradivarius.com/itxrest/3/catalog/store/54009627/50331121/category/{cgid}/product?languageId=-1&showProducts=false&appId=1'
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                headers=self.headers,
                meta={'cgid': cgid}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        productIds = response.json()["productIds"]
        for productId in productIds:
            params = {
                "languageId": "-1",
                "categoryId": response.meta['cgid'],
                "productIds": productId,
                "appId": "1"
            }
            url = "https://www.stradivarius.com/itxrest/3/catalog/store/54009627/50331121/productsArray?" + urlencode(
                params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
                meta={'productId': productId}
            )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        url = 'https://www.stradivarius.com/us/' + response.json()["products"][0]["bundleProductSummaries"][0][
            "productUrl"]
        yield scrapy.Request(
            url=url,
            callback=self.parse_detail,
            headers=self.headers,
            meta={'productId': response.meta['productId']}
        )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        meta = response.meta
        meta['ori_url'] = response.url
        meta['productId'] = meta['productId']
        productId = meta['productId']
        # productId = '397031097'
        # productId = '397031097'
        detail_url = f'https://www.stradivarius.com/itxrest/2/catalog/store/54009627/50331121/category/0/product/{productId}/detail?languageId=-1&appId=1'
        for i in range(6):
            try:
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail_js,
                    headers=self.headers,
                    meta=meta
                )
                break
            except:
                pass

    async def parse_detail_js(self, response, **kwargs):
        global oversold, ori_price, cur_price, stocks, length
        meta = response.meta
        try:
            json_data = response.json()["bundleProductSummaries"][0]
        except:
            json_data = response.json()
        colors = json_data["detail"]["colors"]
        for color in colors:
            itemid = str(json_data["id"]) + str(color["catentryId"])
            skuid = str(json_data["id"]) + str(color["catentryId"])
            breadlist = json_data["productType"]
            title = json_data["name"]
            description = [json_data["detail"]["longDescription"]]
            brand = 'stradivarius'
            oversold_all = not response.json()["isBuyable"]

            sizes = color["sizes"]
            specs = []
            for size in sizes:
                Color = color["name"]
                price = float(str(size["price"])[:-2] + '.' + str(size["price"])[-2:])
                try:
                    origPrice = float(str(size["oldPrice"])[:-2] + '.' + str(size["oldPrice"])[-2:])
                except:
                    origPrice = price
                cur_price = price
                ori_price = origPrice
                for i in range(6):
                    try:
                        r = requests.get(
                            f'https://www.stradivarius.com/itxrest/2/catalog/store/54009627/50331121/product/{json_data["id"]}/stock?languageId=-1&appId=1',
                            headers=self.headers, proxies=self.current_proxies)
                        stocks = json.loads(r.text)["stocks"][0]["stocks"]
                        break
                    except:
                        if i == 5:
                            return
                        pass
                for stock in stocks:
                    if size["sku"] == stock["id"]:
                        if stock["availability"] == 'in_stock':
                            oversold = False
                        else:
                            oversold = True
                spec = {
                    'spec': Color + ' / ' + size["name"],
                    "price": price,
                    "origPrice": origPrice,
                    "priceUnit": "$",
                    "oversold": oversold
                }
                specs.append(spec)

            imgs = []
            images = color["image"]
            url = f'https://static.e-stradivarius.net/5/photos4{images["url"]}'
            img = url + '_1_1_1.jpg'
            imgs.append(img)
            k = 1
            while True:
                img = url + f'_2_{k}_1.jpg'
                for i in range(6):
                    try:
                        length = len(requests.get(img, proxies=self.current_proxies).text)
                        break
                    except:
                        pass
                if length > 200:
                    imgs.append(img)
                    k += 1
                else:
                    break

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
                "detail_url": meta['ori_url'],
                "brand_name": brand,
                "category_info": breadlist,
                "specs": specs,
                "description": description,
                "insert_time": get_now_datetime(),
                "online": True,
                "oversold": oversold_all,
            }

            print(item)
            logger.info(item)

            data = PostData()
            data['dataRows'] = [item]
            data['name'] = 'goods_base'
            data[defaults.DM_SCHEDULER_TASK_ID] = response.meta.get(defaults.DM_SCHEDULER_TASK_ID)
            data[defaults.DM_SCHEDULER_FORCE_TASK] = response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)
            yield data


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl stradivarius:goods_all_list'.split(' '))
