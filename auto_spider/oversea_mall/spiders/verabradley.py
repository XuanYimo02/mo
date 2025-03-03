# -*- coding: utf-8 -*-
# @Time : 2024-05-15 11:16
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
    name = 'verabradley:goods_all_list'
    platform = "verabradley"
    task_id = 'verabradley'
    sch_task = 'verabradley-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'oversea_mall.middlewares.CurlDownloadHandler',
            'https': 'oversea_mall.middlewares.CurlDownloadHandler',
        },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 1,
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
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhcGlLZXkvMjc5MTE1YjciLCJzY29wZSI6eyIyNDQ2MzEyOTkiOlsidzZndDQ0OHh1ZyJdfSwic3RhZ2UiOiJwcm9kIiwicmVnaW9uIjoidXMtZWFzdC0xIiwianRpIjoiZmEzZGQ3YzEtNjJiMi00YTk2LWIxOGItYTAxMTk3NGFlMDhlIiwiaWF0IjoxNzE2MTcxMTY3LCJleHAiOjE3MTYyNTgxNjd9.A_7zBUcBr17cDa4oxBB0sGuB29lx77gHcEs7LPnblfM",
        # "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhcGlLZXkvMjc5MTE1YjciLCJzY29wZSI6eyIyNDQ2MzEyOTkiOlsidzZndDQ0OHh1ZyJdfSwic3RhZ2UiOiJwcm9kIiwicmVnaW9uIjoidXMtZWFzdC0xIiwianRpIjoiZTY5YWEwOWMtMTE5Zi00MDgwLWE2N2QtZmEzMzdmMmYwNWZmIiwiaWF0IjoxNzE2MjU4ODQzLCJleHAiOjE3MTYzNDU4NDN9.YFGZjIY533ju8yTKCKD5LHV9gSKLDKf9A2lv3fcxalc",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://verabradley.com",
        "priority": "u=1, i",
        "referer": "https://verabradley.com/",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
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
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Origin": "https://verabradley.com",
            "Pragma": "no-cache",
            "Referer": "https://verabradley.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "content-type": "application/json",
            "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "x-api-key": "01-279115b7-430d17a368ee9143cc157d644bc7f2be8c5a3ea4"
        }
        url = "https://api.rfksrv.com/account/1/access-token"
        data = {
            "scope": [
                "search-rec"
            ]
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url, headers=headers, data=data, proxies=self.current_proxies)

        json_data = json.loads(response.text)
        accessToken = json_data['accessToken']
        self.headers['authorization'] = 'Bearer ' + accessToken

        urls = [
            'https://verabradley.com/collections/bags',
            'https://verabradley.com/collections/backpacks',
            'https://verabradley.com/collections/travel',
            'https://verabradley.com/collections/accessories',
            'https://verabradley.com/collections/footwear',
            'https://verabradley.com/collections/new-arrivals'
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
        page = 1
        uri = response.url.split('/')[-1]
        params = {
            'data': '{"batch":[{"facet":{"all":true,"total":true,"max":-1},"widget":{"rfkid":"plp_widget"},"content":{"product":{}},"n_item":24,"page_number":%d},{"appearance":{"variables":{}},"widget":{"rfkid":"2-up_promos"}},{"appearance":{"variables":{}},"widget":{"rfkid":"2-up_promos_02"}}],"context":{"page":{"uri":"/collections/%s"},"user":{"uuid":"244631299-nf-yk-40-1p-ivuvxarl1qe2tvx8glhz-1715652731429"}}}' % (page, uri)
        }
        url = "https://api.rfksrv.com/search-rec/12359-244631299/3?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            headers=self.headers,
            meta={'page': page, 'uri': uri}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        page = response.meta['page']
        uri = response.meta['uri']
        values = response.json()["batch"][0]["content"]["product"]["value"]
        for value in values:
            url = value["url"].split('www.')[0] + value["url"].split('www.')[1]
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.parse_detail,
            )

        if len(values):
            page += 1
            params = {
                'data': '{"batch":[{"facet":{"all":true,"total":true,"max":-1},"widget":{"rfkid":"plp_widget"},"content":{"product":{}},"n_item":24,"page_number":%d},{"appearance":{"variables":{}},"widget":{"rfkid":"2-up_promos"}},{"appearance":{"variables":{}},"widget":{"rfkid":"2-up_promos_02"}}],"context":{"page":{"uri":"/collections/%s"},"user":{"uuid":"244631299-nf-yk-40-1p-ivuvxarl1qe2tvx8glhz-1715652731429"}}}' % (
                page, uri)
            }
            url = "https://api.rfksrv.com/search-rec/12359-244631299/3?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
                meta={'page': page, 'uri': uri}
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        meta = response.meta
        meta['ori_url'] = response.url
        detail_url_js = response.url.split('?')[0] + '.js'
        yield scrapy.Request(
            url=detail_url_js,
            callback=self.parse_detail_js,
            headers=self.headers,
            meta=meta
        )

    async def parse_detail_js(self, response, **kwargs):
        try:
            meta = response.meta
            info = response.json()
            itemid = str(info.get('id'))
            skuid = str(info.get('id'))
            title = info.get('title')
            brand = info.get('vendor')
            breadlist = info.get('type')
            cur_price = float(info.get('price')) / 100 if info.get('price') and info.get('price') != 0 else None
            ori_price = float(info.get('compare_at_price')) / 100 if info.get('compare_at_price') and info.get(
                'compare_at_price') != 0 else cur_price
            oversold = False
            ability = info.get('available')
            if ability == False:
                oversold = True

            description = []
            descriptions = info.get('description') if info.get('description') else ''
            if descriptions:
                descriptions = Selector(text=descriptions)
                descriptions = descriptions.xpath("//text()").extract()
                for des in descriptions:
                    des = filter_html_label(des)
                    if des:
                        description.append(des)
            imgs = []
            images = info.get('images') if info.get('images') else []
            for image in images:
                if not image.startswith('http'):
                    image = 'https:' + image
                imgs.append(image)
            specs = []
            skus = info.get('variants') if info.get('variants') else []
            for sku in skus:
                spec = sku.get('title')
                sku_cur_price = float(sku.get('price')) / 100 if sku.get('price') and sku.get('price') != 0 else None
                sku_ori_price = float(sku.get('compare_at_price')) / 100 if sku.get('compare_at_price') and sku.get(
                    'compare_at_price') != 0 else sku_cur_price
                sku_oversold = False
                sku_ability = sku.get('available')
                if sku_ability == False:
                    sku_oversold = True
                if spec:
                    specs_item = {
                        "spec": spec,
                        "price": sku_cur_price,
                        "origPrice": sku_ori_price,
                        "priceUnit": "$",
                        "oversold": sku_oversold,
                    }
                    specs.append(specs_item)

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
                "brand_name": brand,
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


        except Exception as e:
            self.logger.error(f'{response.url} {e} {traceback.format_exc()}')


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl verabradley:goods_all_list'.split(' '))
