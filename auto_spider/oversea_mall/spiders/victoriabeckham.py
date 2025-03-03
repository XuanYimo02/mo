# -*- coding: utf-8 -*-
# @Time : 2024-03-29 10:13
# @Author : Mo

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import warnings
import traceback
from datetime import datetime
from urllib.parse import urljoin
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

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class GoodsAllListSpider(DmSpider):
    name = 'victoriabeckham:goods_all_list'
    platform = "victoriabeckham"
    task_id = 'victoriabeckham'
    sch_task = 'victoriabeckham-task'
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

    proxies = {}
    base_url = ''
    xpath_list = {}
    json_list = {}

    def start_requests(self):
        """
        爬虫首页
        """
        urls = [
            'https://us.victoriabeckham.com/collections/new-arrivals',
            'https://us.victoriabeckham.com/collections/view-all',
            'https://us.victoriabeckham.com/collections/bags',
            'https://us.victoriabeckham.com/collections/view-all-jewellery-accessories',
            'https://us.victoriabeckham.com/collections/shoes',
        ]

        for url in urls:
            page = 1
            url = url + f'?page={page}'
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_home,
                meta={'page': page}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        li_list = response.xpath('//*[@id="product-grid"]/li')
        for li in li_list:
            url = 'https://us.victoriabeckham.com' + li.xpath('./fostr-product-card/div[2]/div/a/@href').extract()[0]
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_detail,
            )
        if len(li_list):
            page += 1
            url = response.url.split('?')[0] + f'?page={page}'
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_home,
                meta={'page': page}
            )

    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """

        pattern = r'window.GloboPreorderParams.product = (.*?});'
        data_start = response.text
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["id"]
        skuid = json_data["id"]
        title = json_data["title"]
        brand = json_data["vendor"]
        breadlist = json_data["type"]
        cur_price = float(str(json_data["price"])[:-2] + '.' + str(json_data["price"])[-2:])
        if json_data["compare_at_price"] == None:
            ori_price = cur_price
        else:
            ori_price = float(str(json_data["compare_at_price"])[:-2] + '.' + str(
                json_data["compare_at_price"])[-2:])
        oversold_all = not json_data["available"]

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
        images = json_data["images"]
        for image in images:
            imgs.append("https:" + image)

        specs = []
        variants = json_data["variants"]
        for variant in variants:
            price = float(str(variant["price"])[:-2] + '.' + str(variant["price"])[-2:])
            if variant["compare_at_price"] == None:
                origPrice = price
            else:
                origPrice = float(str(variant["compare_at_price"])[:-2] + '.' + str(variant["compare_at_price"])[-2:])
            spec = {
                'spec': variant["title"],
                "price": price,
                "origPrice": origPrice,
                "priceUnit": "$",
                "oversold": not variant["available"]
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

    execute('scrapy crawl victoriabeckham:goods_all_list'.split(' '))
