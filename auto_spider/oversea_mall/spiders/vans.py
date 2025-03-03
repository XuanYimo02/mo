# -*- coding: utf-8 -*-
# @Time : 2024-05-31 12:05
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
    name = 'vans:goods_all_list'
    platform = "vans"
    task_id = 'vans'
    sch_task = 'vans-task'
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
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9",
        "brand": "VANS",
        "channel": "ECOMM",
        "locale": "en_US",
        "priority": "u=1, i",
        "referer": "https://www.vans.com/en-us/categories/new-arrivals-c5250?icn=topnav",
        "region": "NORA",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "siteid": "VANS-US",
        "source": "ECOM15",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "x-correlation-id": "63d37952-01bf-4da1-aad3-53f8313a3745",
        "x-dtpc": "11$536163523_940h24vAWOGEFJSHBHHPAJLAUGQFLFUQGKMCDQC-0e0",
        "x-forwarded-headers": "xx-user-agent,xx-forwarded-for",
        "x-transaction-id": "63d37952-01bf-4da1-aad3-53f8313a3745",
        "xx-forwarded-for": "undefined",
        "xx-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
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
            'https://www.vans.com/en-us/categories/new-arrivals-c5250?icn=topnav',
            'https://www.vans.com/en-us/shoes-c00081?icn=topnav',
            'https://www.vans.com/en-us/clothing-c00082?icn=topnav',
            'https://www.vans.com/en-us/accessories-c00083?icn=topnav',
            'https://www.vans.com/en-us/categories/sale-c5410?icn=topnav',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                headers=self.headers
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        cgid = response.url.split('-c')[-1].split('?')[0]
        params = {
            "start": "0",
            "count": "48",
            "sort": "bestMatches",
            "locale": "en-us",
            "filters": f"cgid={cgid}",
            "fqj": "{\"cgid\":\"%s\"}" % cgid
        }
        url = "https://www.vans.com/api/products/v1/catalog?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': 0, 'cgid': cgid},
            headers=self.headers
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        cgid = meta['cgid']
        products = response.json()["products"]
        for product in products:
            url = 'https://www.vans.com' + product["pageUrl"]
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers
            )

        # print(cgid, page, len(products))
        if len(products):
            page += 48
            meta['page'] = page
            meta['cgid'] = cgid
            params = {
                "start": page,
                "count": "48",
                "sort": "bestMatches",
                "locale": "en-us",
                "filters": f"cgid={cgid}",
                "fqj": "{\"cgid\":\"%s\"}" % cgid
            }
            url = "https://www.vans.com/api/products/v1/catalog?" + urlencode(params)
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
        meta = response.meta
        meta['ori_url'] = response.url
        imgs = []
        li_list = response.xpath('//*[@id="template-pdp-enabled"]/div[3]/div/div[2]/div/div/div[2]/ul/li')
        for li in li_list:
            try:
                img = li.xpath('./div/button[1]/@data-image-hr').extract()[0].split('(\'')[-1].split('\')')[0]
                imgs.append(img)
            except:
                pass
        meta['imgs'] = imgs

        cgid = response.url.split('-p')[-1].upper()
        detail_url_js = f'https://www.vans.com/api/products/v1/products/{cgid}/details?locale=en-us'
        yield scrapy.Request(
            url=detail_url_js,
            callback=self.parse_detail_js,
            headers=self.headers,
            meta=meta
        )

    async def parse_detail_js(self, response, **kwargs):
        meta = response.meta
        info = response.json()
        itemid = info["id"]
        skuid = info["sku"]
        title = info["name"]
        breadlist = info["primary_category_name"]
        cur_price = info["variants"][0]["price"]["current"]
        ori_price = info["variants"][0]["price"]["original"]
        color = info["colorCode"]
        oversold = True
        ability = info["productInventoryState"]
        if ability == 'InStock':
            oversold = False

        description = []
        descriptions = info.get('description') if info.get('description') else ''
        if descriptions:
            descriptions = Selector(text=descriptions)
            descriptions = descriptions.xpath("//text()").extract()
            for des in descriptions:
                des = filter_html_label(des)
                if des:
                    description.append(des)

        specs = []
        skus = info["attributes"][0]["options"]
        for sku in skus:
            spec = sku["altLabel1"]
            sku_oversold = not sku["available"]
            if spec:
                specs_item = {
                    "spec": color + ' / ' + spec,
                    "price": cur_price,
                    "origPrice": ori_price,
                    "priceUnit": "$",
                    "oversold": sku_oversold,
                }
                specs.append(specs_item)

        imgs = meta['imgs']
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": itemid,
            "skuid": skuid,
            "title": title,
            "description": description,
            "price": cur_price,
            "orig_price": ori_price,
            "price_unit": "$",
            "prices": {"US": {"p": cur_price, "o": ori_price, 'u': "$"}},
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": meta['ori_url'],
            "brand_name": 'VANS',
            "category_info": breadlist,
            "specs": specs,
            "insert_time": get_now_datetime(),
            "online": True,
            "oversold": oversold,
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

    execute('scrapy crawl vans:goods_all_list'.split(' '))
