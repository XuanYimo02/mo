# -*- coding: utf-8 -*-
# @Time : 2024-04-26 16:26
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
    num = 0
    name = 'olivela:goods_all_list'
    platform = "olivela"
    task_id = 'olivela'
    sch_task = 'olivela-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
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

    proxies = {}
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        urls = [
            'https://www.olivela.com/women/clothing',
            # 'https://www.olivela.com/jewelry-watches',
            # 'https://www.olivela.com/beauty',
            # 'https://www.olivela.com/women/shoes',
            # 'https://www.olivela.com/women/bags-accessories',
            # 'https://www.olivela.com/home-gifts',
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
        params = {
            "x-algolia-agent": "Algolia for JavaScript (4.23.3); Browser (lite); instantsearch.js (4.56.8); react (18.2.0); react-instantsearch (6.47.3); react-instantsearch-hooks (6.47.3); next.js (12.3.4); JS Helper (3.14.0)",
            "x-algolia-api-key": "15f0547a6287ff6af05a37a9c17d4b33",
            "x-algolia-application-id": "HQVOQMXDDN"
        }
        data = {
            "requests": [
                {
                    "indexName": "products",
                    "params": f"clickAnalytics=true&facetFilters=%5B%5B%22named_tags.categories.lvl0%3AJewelry%20%26%20watches%22%5D%5D&facets=%5B%22*%22%5D&filters=inventory_quantity%3E0&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&page={page}&query=&tagFilters=&userToken=119994103_1714036561"
                },
                {
                    "indexName": "products",
                    "params": f"analytics=false&clickAnalytics=false&facets=named_tags.categories.lvl0&filters=inventory_quantity%3E0&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&page={page}&query=&userToken=119994103_1714036561"
                }
            ]
        }
        data = json.dumps(data, separators=(',', ':'))

        url = "https://hqvoqmxddn-dsn.algolia.net/1/indexes/*/queries?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': page},
            method='POST',
            body=data
        )



    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        page = response.meta['page']

        hits = response.json()["results"][0]["hits"]
        for hit in hits:
            url = 'https://www.olivela.com/products/' + hit['handle']
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        hits = response.json()["results"][1]["hits"]
        for hit in hits:
            url = 'https://www.olivela.com/products/' + hit['handle']
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        if len(hits):
            page += 1
            params = {
                "x-algolia-agent": "Algolia for JavaScript (4.23.3); Browser (lite); instantsearch.js (4.56.8); react (18.2.0); react-instantsearch (6.47.3); react-instantsearch-hooks (6.47.3); next.js (12.3.4); JS Helper (3.14.0)",
                "x-algolia-api-key": "15f0547a6287ff6af05a37a9c17d4b33",
                "x-algolia-application-id": "HQVOQMXDDN"
            }
            data = {
                "requests": [
                    {
                        "indexName": "products",
                        "params": f"clickAnalytics=true&facetFilters=%5B%5B%22named_tags.categories.lvl0%3AJewelry%20%26%20watches%22%5D%5D&facets=%5B%22*%22%5D&filters=inventory_quantity%3E0&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&page={page}&query=&tagFilters=&userToken=119994103_1714036561"
                    },
                    {
                        "indexName": "products",
                        "params": f"analytics=false&clickAnalytics=false&facets=named_tags.categories.lvl0&filters=inventory_quantity%3E0&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&page={page}&query=&userToken=119994103_1714036561"
                    }
                ]
            }
            data = json.dumps(data, separators=(',', ':'))

            url = "https://hqvoqmxddn-dsn.algolia.net/1/indexes/*/queries?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta={'page': page},
                method='POST',
                body=data
            )


    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script></body></html>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        json_data = json_data["props"]["pageProps"]['product']

        itemid = json_data["id"].split('/')[-1]
        skuid = json_data["id"].split('/')[-1]
        title = json_data["title"]
        brand = json_data["vendor"]
        breadlist = json_data["productType"]
        oversold_all = not json_data["availableForSale"]

        description = []
        description_data = json_data["description"]
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
        imgs_list = response.xpath('//*[@class="slider-wrapper"]/div/div[2]/div[2]/div/div/div')
        if len(imgs_list) == 0:
            imgs = [json_data["featuredImage"]["src"]]
        else:
            for image in imgs_list:
                img = image.xpath('./div/div/img/@srcset').extract()[-1]
                pattern = r'2048w, (.*?) 3840w,'
                img = re.search(pattern, img).group(1)
                if float(image.xpath('./@data-index').extract()[0]) <= 0:
                    imgs.append(img)

        specs = []
        variants = json_data["variants"]["edges"]
        for variant in variants:
            price = float(variant["node"]["priceV2"]["amount"])
            if variant["node"]["compareAtPriceV2"]["amount"] == "0.0":
                origPrice = price
            else:
                origPrice = float(variant["node"]["compareAtPriceV2"]["amount"])
            cur_price = price
            ori_price = origPrice
            spec = {
                'spec': variant["node"]["title"],
                "price": price,
                "origPrice": origPrice,
                "priceUnit": "$",
                "oversold": not variant["node"]["availableForSale"]
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

    execute('scrapy crawl olivela:goods_all_list'.split(' '))
