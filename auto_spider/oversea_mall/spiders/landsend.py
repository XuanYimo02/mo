# -*- coding: utf-8 -*-
# @Time : 2024-05-28 11:48
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
    name = 'landsend:goods_all_list'
    platform = "landsend"
    task_id = 'landsend'
    sch_task = 'landsend-task'
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

    headers = {
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "Accept": "application/json, text/plain, */*",
        "x-dtpc": "12$267818572_374h9vRQQUVVMHELFSWDCJVKIAGCMAFDRRNPPF-0e0",
        "Referer": "https://www.landsend.com/products/mens-short-sleeve-cotton-supima-polo-shirt/id_248707?attributes=11440,43307,44255,44967",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": "\"Windows\""
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
            'https://www.landsend.com/shop/mens-clothing/S-xez-y5b-xec',
            'https://www.landsend.com/shop/womens-clothing/S-xez-y5c-xec',
            'https://www.landsend.com/shop/swimsuits/S-xfh-xez-xec',
            'https://www.landsend.com/shop/girls/S-y5d-xec',
            'https://www.landsend.com/shop/boys/S-y5e-xec',
            'https://www.landsend.com/shop/backpacks-kids/S-xgw-xfd-yuh-xec',
            'https://www.landsend.com/shop/kids-shoes/S-xfm-xf0-yuh-xec',
            'https://www.landsend.com/shop/accessories-kids/S-xf1-yuh-xec',
            'https://www.landsend.com/shop/outerwear/S-xfi-xez-xec',
            'https://www.landsend.com/shop/shoes/S-xfm-xf0-xec',
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
        gid = response.url.split('/')[-1]
        params = {
            "searchContext": "generic",
            "needReturnRefinements": "true",
            "pageSize": "96",
            "pageOffset": "0",
            "sort": "",
            "priceClarityEnabled": "true",
            "promoCode": "MEMORIAL"
        }
        url = f"https://www.landsend.com/api/search/shop/{gid}?" + urlencode(params)
        meta = {'page': 0, 'gid': gid}
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta=meta
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        gid = meta['gid']
        products = response.json()["productResult"]["products"]
        for product in products:
            try:
                url = 'https://www.landsend.com' + product["productUrl"]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        # print(len(products), response)
        if len(products):
            page += 96
            params = {
                "searchContext": "generic",
                "needReturnRefinements": "true",
                "pageSize": "96",
                "pageOffset": str(page),
                "sort": "",
                "priceClarityEnabled": "true",
                "promoCode": "MEMORIAL"
            }
            url = f"https://www.landsend.com/api/search/shop/{gid}?" + urlencode(params)
            meta['page'] = page
            meta['gid'] = gid
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
        meta = response.meta
        productId = response.url.split('id_')[-1].split('?')[0]
        meta['ori_url'] = response.url.split('?')[0]
        params = {
            "productId": str(productId),
            "promoCode": "MEMORIAL"
        }
        detail_url_js = "https://www.landsend.com/le-api/pub/product-lookup/product?" + urlencode(params)
        yield scrapy.Request(
            url=detail_url_js,
            callback=self.parse_detail_js,
            meta=meta,
            dont_filter=True
        )

    async def parse_detail_js(self, response, **kwargs):

        itemid = str(response.json()["productDetail"]["number"])
        title = response.json()["pageMetaOverride"]["pageTitle"].split(' | ')[0]
        brand = response.json()["productDetail"]["brandName"]
        breadlist = ''
        categoryPaths = response.json()["productDetail"]["categoryPaths"]
        for categoryPath in categoryPaths:
            if categoryPath == categoryPaths[0]:
                breadlist = categoryPath["name"]
            else:
                breadlist += ' / ' + categoryPath["name"]

        li = []
        skus = response.json()["productDetail"]["skus"]
        for sk in skus:
            skuid = str(sk["color"]["values"][0]["number"])
            if skuid not in li:
                li.append(skuid)
                detail_url = response.meta['ori_url'] + '?attributes=' + skuid
                cur_price = sk["price"]["currentPrice"]
                ori_price = sk["price"]["originalPrice"]
                oversold_all = True
                productCopies = response.json()["productDetail"]["productCopies"]
                description = []
                for productCopy in productCopies:
                    if productCopy["number"] == sk["styleNumber"]:
                        description = productCopy["featureBullets"]

                imgs = []
                images = sk["images"]
                for image in images:
                    img = 'https://' + image["imageUrl"]
                    imgs.append(img)

                specs = []
                for sku in skus:
                    if str(sku["color"]["values"][0]["number"]) == skuid:
                        status = sku["warehouseInventoryStatus"][0]["status"]
                        if status == 'N':
                            oversold = True
                        else:
                            oversold = False
                            oversold_all = False
                        try:
                            size = sku["size"]["values"][0]["label"]
                            color = sku["color"]["values"][0]["label"]
                            spec = {
                                'spec': color + ' / ' + size,
                                "price": sku["price"]["currentPrice"],
                                "origPrice": sku["price"]["originalPrice"],
                                "priceUnit": "$",
                                "oversold": oversold
                            }
                        except:
                            color = sku["color"]["values"][0]["label"]
                            spec = {
                                'spec': color,
                                "price": sku["price"]["currentPrice"],
                                "origPrice": sku["price"]["originalPrice"],
                                "priceUnit": "$",
                                "oversold": oversold
                            }
                        specs.append(spec)

                oss_imgs = get_oss_imgs(self.platform, imgs)
                await download_imgs(self.platform, imgs, skuid)
                item = {
                    "platform": self.platform,
                    "itemid": itemid,
                    "skuid": itemid + skuid,
                    "title": title,
                    "price": cur_price,
                    "orig_price": ori_price,
                    "price_unit": "$",
                    "prices": {"US": {"p": cur_price, "o": ori_price, 'u': "$"}},
                    "imgs": oss_imgs,
                    "pic_url": oss_imgs[0],
                    "orig_imgs": imgs,
                    "orig_main_pic": imgs[0],
                    "detail_url": detail_url,
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

    execute('scrapy crawl landsend:goods_all_list'.split(' '))
