# -*- coding: utf-8 -*-
# @Time : 2024-05-20 10:43
# @Author : Mo

import logging
import os
import sys

from scrapy import Selector

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
    name = 'arcteryx:goods_all_list'
    platform = "arcteryx"
    task_id = 'arcteryx'
    sch_task = 'arcteryx-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
            # "oversea_mall.middlewares.OverseaDMProxyMiddleware": 200,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
            'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 10,
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
        "content-type": "application/json",
        "origin": "https://arcteryx.com",
        "priority": "u=1, i",
        "referer": "https://arcteryx.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
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
        # urls = [
        #     'https://arcteryx.com/us/en/c/mens',
        # ]
        keys = [
            'men',
            'women',
            'footwear'
        ]
        for key in keys:
            params = {
                "account_id": "7358",
                "domain_key": "arcteryx",
                "fl": "analytics_name,collection,colour_images_map,colour_images_map_us,description,discount_price_us,gender,hover_image,is_new,is_pro,is_revised,price_us,pid,review_count,rating,slug,title,thumb_image",
                "_br_uid_2": "uid=2986200498792:v=15.0:ts=1715573904783:hc=27",
                "url": "https://arcteryx.com/us/en/c/mens/shell-jackets",
                "rows": "200",
                "start": "0",
                "view_id": "us",
                "request_type": "search",
                "search_type": "category",
                "q": key
            }
            url = "https://core.dxpapi.com/api/v1/core/?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                headers=self.headers,
                meta={'page': 0, 'key': key}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        meta = response.meta
        page = meta['page']
        key = meta['key']

        docs = response.json()["response"]["docs"]
        for doc in docs:
            try:
                url = 'https://arcteryx.com/us/en/shop/' + doc["slug"]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers
                )
            except:
                pass

        if len(docs):
            page += 1
            params = {
                "account_id": "7358",
                "domain_key": "arcteryx",
                "fl": "analytics_name,collection,colour_images_map,colour_images_map_us,description,discount_price_us,gender,hover_image,is_new,is_pro,is_revised,price_us,pid,review_count,rating,slug,title,thumb_image",
                # "efq": "genders:(\"men\")",
                "_br_uid_2": "uid=2986200498792:v=15.0:ts=1715573904783:hc=27",
                "url": "https://arcteryx.com/us/en/c/mens/shell-jackets",
                "rows": "200",
                "start": str(200*page),
                "view_id": "us",
                "request_type": "search",
                "search_type": "category",
                "q": key
            }
            url = "https://core.dxpapi.com/api/v1/core/?" + urlencode(params)
            meta['page'] = page
            meta['key'] = key
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta=meta
            )


    # async def parse_list(self, response, **kwargs):
    #     """
    #     爬虫列表页抓取
    #     """

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        print(response)
        global breadlist
        pattern = 'type="application/json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        product = json.loads(json_data["props"]["pageProps"]["product"])
        item_list = product["colourOptions"]["options"]
        title = product["analyticsName"]
        ori_price = product["price"]
        cur_price = product["discountPrice"]
        if cur_price == None:
            cur_price = ori_price

        description = []
        descriptions = product["description"] if product["description"] else ''
        if descriptions:
            descriptions = Selector(text=descriptions)
            descriptions = descriptions.xpath("//text()").extract()
            for des in descriptions:
                des = filter_html_label(des)
                if des:
                    description.append(des)

        breadcrumbs = product["breadcrumbs"]
        for breadcrumb in breadcrumbs[1:]:
            if breadcrumb == breadcrumbs[1]:
                breadlist = breadcrumb["label"]
            else:
                breadlist += ' / ' + breadcrumb["label"]
        brand = self.platform
        oversold_all = True

        variants = product["variants"]
        size_list = product["sizeOptions"]["options"]
        detailedImages = product["detailedImages"]

        for item in item_list:
            itemid = product["id"]
            value = item["value"]
            skuid = itemid + value
            color = item["label"]
            specs = []
            imgs = []
            for variant in variants:
                if variant["colourId"] == value:
                    origPrice = variant["price"]
                    price = variant["discountPrice"]
                    if price == None:
                        price = origPrice
                    inventory = variant["inventory"]
                    if inventory:
                        oversold = False
                    else:
                        oversold = True
                    if oversold == False:
                        oversold_all = False


                    for size in size_list:
                        if size["value"] == variant["sizeId"]:
                            spec = {
                                'spec': color + ' / ' + size["label"],
                                "price": price,
                                "origPrice": origPrice,
                                "priceUnit": "$",
                                "oversold": oversold
                            }
                            specs.append(spec)

            for detailedImage in detailedImages:
                if detailedImage["colourLabel"] == color:
                    image = detailedImage["url"]
                    imgs.append(image)
            if imgs == []:
                image = product["colourOptions"]["options"][0]["image"]["url"]
                imgs.append(image)

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

    execute('scrapy crawl arcteryx:goods_all_list'.split(' '))
