# -*- coding: utf-8 -*-
# @Time : 2024-05-23 17:43
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
    name = 'cupshe:goods_all_list'
    platform = "cupshe"
    task_id = 'cupshe'
    sch_task = 'cupshe-task'
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
            'https://www.cupshe.com/collections/one-piece?icn=allonepieces&ici=vacationnavbaronepiece_allonepieces',
            'https://www.cupshe.com/collections/bikinis?icn=allbikinis&ici=vacationnavbarbikinis_allbikinis',
            'https://www.cupshe.com/collections/vacationdress?icn=alldresses&ici=vacationnavbardresses_alldresses',
            'https://www.cupshe.com/collections/cover-up-1?icn=shopall&ici=vacationnavbarcoverups_shopall',
            'https://www.cupshe.com/collections/allbestsellersvacation?icn=allclothing&ici=vacationnavbarclothing_allclothing',
            'https://www.cupshe.com/collections/new-arrivals?icn=allnew&ici=vacationnavbarnew_allnew',
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
        seoUrl = response.url.split('?')[0].split('/')[-1]
        params = {
            "subTerminal": "1",
            "skcPriceList": "",
            "sortId": "1",
            "pageNum": "1",
            "pageSize": "48",
            "seoUrl": seoUrl,
            "conditionFilter": "",
            "distinctId": "34b670bd-134b-47f2-8608-40a8e7491a0b",
            "abType": "custom-ranking-price-1",
            "peopleType": "1",
            "visitorType": "1,4",
            "siteId": "1",
            "channelId": "1",
            "brandId": "1",
            "terminalId": "1",
            "loginMethod": "0",
            "lang": "en-GB",
            "langCode": "en-GB",
            "klarnaCode": "en-US",
            "klarnaCodeEn": "en-US",
            "nuveiLangCode": "en",
            "currency": "USD",
            "currencyCode": "$",
            "shopId": "1",
            "siteName": "us",
            "currencyPosition": "left",
            "numTypeLike": "en",
            "calcDiscountMethod": "calcDiscountWithoutOff",
            "userSelectLang": "1",
            "themeType": "vacation",
            "userSelectCurrency": "1"
        }
        url = "https://bff-shopify.cupshe.com/service/col/page?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': 1, 'seoUrl': seoUrl}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        seoUrl = meta['seoUrl']

        dataDetail = response.json()["data"]["dataDetail"]
        for data in dataDetail:
            try:
                url = 'https://www.cupshe.com/products/' + data["skcs"][0]["jumpPath"]
                skcCode = data["skcs"][0]["skcCode"]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers,
                    meta={'skcCode': skcCode}
                )
            except:
                pass

        if len(dataDetail):
            page += 1
            params = {
                "subTerminal": "1",
                "skcPriceList": "",
                "sortId": "1",
                "pageNum": str(page),
                "pageSize": "48",
                "seoUrl": seoUrl,
                "conditionFilter": "",
                "distinctId": "34b670bd-134b-47f2-8608-40a8e7491a0b",
                "abType": "custom-ranking-price-1",
                "peopleType": "1",
                "visitorType": "1,4",
                "siteId": "1",
                "channelId": "1",
                "brandId": "1",
                "terminalId": "1",
                "loginMethod": "0",
                "lang": "en-GB",
                "langCode": "en-GB",
                "klarnaCode": "en-US",
                "klarnaCodeEn": "en-US",
                "nuveiLangCode": "en",
                "currency": "USD",
                "currencyCode": "$",
                "shopId": "1",
                "siteName": "us",
                "currencyPosition": "left",
                "numTypeLike": "en",
                "calcDiscountMethod": "calcDiscountWithoutOff",
                "userSelectLang": "1",
                "themeType": "vacation",
                "userSelectCurrency": "1"
            }
            url = "https://bff-shopify.cupshe.com/service/col/page?" + urlencode(params)
            meta['page'] = page
            meta['seoUrl'] = seoUrl
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
        skcCode = response.meta['skcCode']
        params = {
            "subTerminal": "1",
            "skcCode": f"{skcCode}",
            "source": "1",
            "siteId": "1",
            "channelId": "1",
            "brandId": "1",
            "terminalId": "1",
            "loginMethod": "0",
            "lang": "en-GB",
            "langCode": "en-GB",
            "klarnaCode": "en-US",
            "klarnaCodeEn": "en-US",
            "nuveiLangCode": "en",
            "currency": "USD",
            "currencyCode": "$",
            "shopId": "1",
            "siteName": "us",
            "currencyPosition": "left",
            "numTypeLike": "en",
            "calcDiscountMethod": "calcDiscountWithoutOff",
            "userSelectLang": "1",
            "themeType": "vacation",
            "userSelectCurrency": "1",
            "visitorType": "0,4",
            "peopleType": "0"
        }
        url = "https://cfs.cupshe.com/commodity/selfbuild/detail?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_detail_js,
            meta={'ori_url': response.url}
        )

    async def parse_detail_js(self, response, **kwargs):
        global cur_price, ori_price
        json_data = response.json()
        itemid = json_data["data"]["spuCode"]
        skuid = json_data["data"]["skcCode"]
        commodities = json_data["data"]["commodities"]
        oversold_all = True
        for commodity in commodities:
            if commodity['skcCode'] == skuid:
                title = commodity["title"]
                brand = self.platform
                breadlist = commodity["productType"]["productTypeName"]

                description = []
                descriptions = commodity["description"] if commodity["description"] else ''
                if descriptions:
                    descriptions = Selector(text=descriptions)
                    descriptions = descriptions.xpath("//text()").extract()
                    for des in descriptions:
                        des = filter_html_label(des)
                        if des:
                            description.append(des)

                imgs = []
                images = commodity["medias"]
                for image in images:
                    img = image["src"]
                    imgs.append(img)

                specs = []
                variants = commodity["virtualSkuMap"]
                color = commodity["color"]
                for key, variant in variants.items():
                    price = variant["discountPrice"]
                    if variant["retailPriceStr"] == '':
                        origPrice = price
                    else:
                        origPrice = float(variant['retailPriceStr'])
                    cur_price = price
                    ori_price = origPrice
                    if variant["hasInventory"] == True:
                        oversold_all = False
                    spec = {
                        'spec': color + ' / ' + variant["size"],
                        "price": price,
                        "origPrice": origPrice,
                        "priceUnit": "$",
                        "oversold": not variant["hasInventory"]
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
                    "detail_url": response.meta['ori_url'],
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

    execute('scrapy crawl cupshe:goods_all_list'.split(' '))
