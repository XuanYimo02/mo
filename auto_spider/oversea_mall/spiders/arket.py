# -*- coding: utf-8 -*-
# @Time : 2024-05-27 16:57
# @Author : Mo

import logging
import os
import subprocess
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
import json
import subprocess
import time
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs
import requests
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class GoodsAllListSpider(DmSpider, AutoParse):
    name = 'arket:goods_all_list'
    platform = "arket"
    task_id = 'arket'
    sch_task = 'arket-task'
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
        "DOWNLOAD_DELAY": 3,
        'DOWNLOAD_TIMEOUT': 10,
        "LOG_LEVEL": "INFO",
        "EXIT_ENABLED": True,
        'LOG_FILE': log_file_path,
        'LOG_STDOUT': False,
        'REDIRECT_ENABLED': False
    }

    headers = {
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "Accept": "*/*",
        "Referer": "https://www.arket.com/en/women/all.html",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": "\"Windows\""
    }
    cookies = {
        "HMCORP_locale": "en_WW",
        "ecom_country": "ww",
        "ecom_locale": "en_ww",
        "HMCORP_currency": "USD",
    }
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        params = {
            "start": "0"
        }
        urls = [
            "https://www.arket.com/en/women/all/_jcr_content/homepagepar/widthcomponent/o-width/productlisting.products.html?" + urlencode(params),
            'https://www.arket.com/en/men/all/_jcr_content/homepagepar/widthcomponent/o-width/productlisting.products.html?' + urlencode(params),
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                headers=self.headers,
                cookies=self.cookies,
                meta={'page': 0}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        div_list = response.xpath('//*[@id="reloadProducts"]/div')
        for div in div_list:
            try:
                url = div.xpath('./a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers,
                    cookies=self.cookies
                )
            except:
                pass

        if len(div_list):
            page += 36
            params = {
                "start": page
            }
            url = "https://www.arket.com/en/women/all/_jcr_content/homepagepar/widthcomponent/o-width/productlisting.products.html?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page},
                headers=self.headers,
                cookies=self.cookies
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        # print(response)
        # return

        global oversold
        js_code = """
        var productArticleDetails = ********
        function get_data() {
            return JSON.stringify(productArticleDetails);
        }
        """
        pattern = r'var productArticleDetails =(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = result.group(1)

        js_code = js_code.replace('********', json_data)
        js_code = re.sub(r"'modelHeight': '.*?',", "'modelHeight': '',", js_code)
        ctx = execjs.compile(js_code)
        result = ctx.call("get_data")
        json_data = json.loads(result)

        itemid = json_data["articleCode"]
        skuid = json_data["articleCode"]
        title = json_data["name"]
        color = json_data[skuid]["colorLoc"]
        description = [json_data[skuid]["description"]]
        brand = json_data[skuid]["brandName"]
        if brand == '':
            brand = self.platform
        breadlist = json_data["categoryParentKey"].replace('/1/', '')

        cur_price = float(json_data[skuid]["priceValue"])
        ori_price = json_data[skuid]["priceSaleValue"]
        if ori_price == None:
            ori_price = cur_price
        else:
            ori_price = float(ori_price)

        imgs = []
        images = json_data[skuid]["vAssets"]
        for image in images:
            img = 'https:' + image["thumbnail"]
            imgs.append(img)

        oversold_all = True
        pattern = r'</script><script id="product-schema" type="application/ld\+json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        available_data = json.loads(re.sub(r'"url":".*?",', '"url":"",', result.group(1)))
        offers = available_data["offers"]
        specs = []
        variants = json_data[skuid]["variants"]
        for variant in variants:
            variantCode = variant['variantCode']
            for offer in offers:
                if offer['sku'] == variantCode:
                    if 'InStock' in offer['availability']:
                        oversold_all = False
                        oversold = False
                    else:
                        oversold = True
            spec = {
                'spec': color + ' / ' + variant["sizeName"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": oversold
            }
            specs.append(spec)


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

    execute('scrapy crawl arket:goods_all_list'.split(' '))
