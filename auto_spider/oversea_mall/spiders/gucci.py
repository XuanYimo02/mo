# -*- coding: utf-8 -*-
# @Time : 2024-05-30 11:23
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
    name = 'gucci:goods_all_list'
    platform = "gucci"
    task_id = 'gucci'
    sch_task = 'gucci-task'
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
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=1, i",
        "referer": "https://www.gucci.com/us/en/ca/women/gucci-summer-collection-for-women-c-summer-collection-women",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
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
            'https://www.gucci.com/us/en/ca/whats-new/new-in/this-week-women-c-new-women',
            'https://www.gucci.com/us/en/ca/whats-new/new-in/this-week-men-c-new-men',
            'https://www.gucci.com/us/en/ca/women/gucci-summer-collection-for-women-c-summer-collection-women',
            'https://www.gucci.com/us/en/ca/men/gucci-summer-collection-for-men-c-summer-collection-men',
            'https://www.gucci.com/us/en/ca/whats-new/gucci-rosso-ancora-selection-c-rosso-ancora-selection',
            'https://www.gucci.com/us/en/ca/women/summer-handbags-c-women-summer-handbags',
            'https://www.gucci.com/us/en/ca/women/summer-shoes-c-women-summer-shoes',
            'https://www.gucci.com/us/en/ca/men/summer-shoes-c-men-summer-shoes',
            'https://www.gucci.com/us/en/ca/women/handbags-c-women-handbags',
            'https://www.gucci.com/us/en/ca/women/travel-for-women-c-women-accessories-lifestyle-bags-and-luggage',
            'https://www.gucci.com/us/en/ca/men/travel-for-men-c-men-bags-luggage',
            'https://www.gucci.com/us/en/ca/gifts/gifts-for-women-c-gifts-for-her',
            'https://www.gucci.com/us/en/ca/beauty/gift-ideas-c-beauty-gift-ideas',
            'https://www.gucci.com/us/en/ca/women/handbags/mini-bags-for-women-c-women-handbags-mini-bags',
            'https://www.gucci.com/us/en/ca/women/handbags/shoulder-bags-for-women-c-women-handbags-shoulder-bags',
            'https://www.gucci.com/us/en/ca/women/handbags/tote-bags-for-women-c-women-handbags-totes',
            'https://www.gucci.com/us/en/ca/women/handbags/backpacks-belt-bags-for-women-c-women-handbags-backpacks',
            'https://www.gucci.com/us/en/ca/women/handbags/top-handle-bags-for-women-c-women-handbags-top-handles-and-boston-bags',
            'https://www.gucci.com/us/en/ca/women/handbags/clutches-evening-bags-for-women-c-women-handbags-clutches',
            'https://www.gucci.com/us/en/ca/men/new-mens-collection-c-new-men-collection-2024',
            'https://www.gucci.com/us/en/ca/gifts/gifts-for-men-c-gifts-for-him',
            'https://www.gucci.com/us/en/ca/men/bags-for-men-c-men-bags',
            'https://www.gucci.com/us/en/ca/men/ready-to-wear-for-men-c-men-readytowear',
            'https://www.gucci.com/us/en/ca/men/shoes-for-men-c-men-shoes',
            'https://www.gucci.com/us/en/ca/men/wallets-and-small-accessories-for-men-c-men-accessories-wallets',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/belts-for-men-c-men-accessories-belts',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/eyewear-for-men-c-men-eyewear',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/ties-for-men-c-men-accessories-ties',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/scarves-for-men-c-men-accessories-scarves',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/hats-and-gloves-for-men-c-men-accessories-hats-and-gloves',
            'https://www.gucci.com/us/en/ca/men/accessories-for-men/socks-for-men-c-men-accessories-socks',
            'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-men-c-jewelry-watches-watches-men',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-jewelry-for-men-c-jewelry-watches-fine-jewelry-men',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-jewelry-for-men-c-jewelry-watches-silver-jewelry-men',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-jewelry-for-men-c-jewelry-watches-fashion-jewelry-men',
            'https://www.gucci.com/us/en/ca/children/baby-c-children-baby',
            'https://www.gucci.com/us/en/ca/children/girls-c-children-girls',
            'https://www.gucci.com/us/en/ca/children/boys-c-children-boys',
            'https://www.gucci.com/us/en/ca/gifts/gifts-for-children-c-gifts-for-children',
            'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-women-c-jewelry-watches-watches-women',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-jewelry-for-women-c-jewelry-watches-fine-jewelry-women',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-jewelry-for-men-c-jewelry-watches-fine-jewelry-men',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-rings-c-jewelry-watches-fine-jewelry-rings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-necklaces-c-jewelry-watches-fine-jewelry-necklaces',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-bracelets-c-jewelry-watches-fine-jewelry-bracelets',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-earrings-c-jewelry-watches-fine-jewelry-earrings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-jewelry-for-women-c-jewelry-watches-fashion-jewelry-women',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-rings-c-jewelry-watches-fashion-jewelry-rings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-necklaces-c-jewelry-watches-fashion-jewelry-necklaces',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-bracelets-c-jewelry-watches-fashion-jewelry-bracelets',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-earrings-c-jewelry-watches-fashion-jewelry-earrings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-hair-accessories-c-jewelry-watches-fashion-jewelry-hair-accessories',
            'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-brooches-pins-c-jewelry-watches-fashion-jewelry-brooches-pins',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-jewelry-for-women-c-jewelry-watches-silver-jewelry-women',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-rings-c-jewelry-watches-silver-jewelry-rings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-necklaces-c-jewelry-watches-silver-jewelry-necklaces',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-bracelets-c-jewelry-watches-silver-jewelry-bracelets',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-earrings-c-jewelry-watches-silver-jewelry-earrings',
            'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-cufflinks-other-accessories-c-jewelry-watches-silver-jewelry-cufflinks',
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
        categoryCode = response.url.split('-c-')[-1]
        params = {
            "categoryCode": categoryCode,
            "show": "Page",
            "page": "0"
        }
        url = "https://www.gucci.com/us/en/c/productgrid?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            headers=self.headers,
            meta={'page': 0, 'categoryCode': categoryCode}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        categoryCode = meta['categoryCode']
        items = response.json()["products"]["items"]
        for item in items:
            try:
                url = 'https://www.gucci.com/us/en' + item["productLink"]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers
                )
            except:
                pass

        # print(categoryCode, page, len(items))
        if len(items):
            page += 1
            meta['page'] = page
            meta['categoryCode'] = categoryCode
            params = {
                "categoryCode": categoryCode,
                "show": "Page",
                "page": page
            }
            url = "https://www.gucci.com/us/en/c/productgrid?" + urlencode(params)
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
        global ori_price, cur_price, breadlist
        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = result.group(1)
        json_data = json.loads(json_data)

        itemid = json_data["sku"]
        skuid = json_data["sku"]
        title = json_data["name"]
        description = [json_data["description"]]
        brand = json_data["brand"]["name"]
        bread_list = response.url.split('https://www.gucci.com/us/en/pr/')[-1].split('/')
        for bread in bread_list[:-1]:
            if bread == bread_list[0]:
                breadlist = bread
            else:
                breadlist += ' / ' + bread

        imgs = []
        images = json_data["image"]
        for image in images:
            imgs.append(image)

        specs = []
        oversold_all = True
        variants = json_data["offers"]
        for variant in variants:
            cur_price = float(variant["price"])
            ori_price = cur_price
            availability = variant["availability"]
            if availability == 'InStock':
                oversold = False
                oversold_all = False
            else:
                oversold = True
            spec = {
                'spec': variant["sku"].split('_')[-1],
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

    async def parse_detail_js(self, response, **kwargs):
        pass


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl gucci:goods_all_list'.split(' '))
