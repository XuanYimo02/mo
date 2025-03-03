# -*- coding: utf-8 -*-
# @Time : 2024-06-19 10:37
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
    name = 'miinto:goods_all_list'
    platform = "miinto"
    task_id = 'miinto'
    sch_task = 'miinto-task'
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
        "DOWNLOAD_DELAY": 1,
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
        page = 1
        urls = [
            'https://www.miinto.com/women?page=1',
            'https://www.miinto.com/men?page=1',
            'https://www.miinto.com/kids?page=1',
            'https://www.miinto.com/sport?page=1'
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        div_list = response.xpath('//*[@id="mf-plp-root"]/div/div[1]/div[2]/div[3]/div')
        for div in div_list:
            try:
                url = 'https://www.miinto.com' + div.xpath('./a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        print(len(div_list), response)
        if len(div_list):
            page += 1
            url = response.url.split('?')[0] + '?page=%d' % page
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page}
            )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'window.__PDP_PRELOADED_STATE__ = JSON.stringify\((.*?)\);'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["product"]["id"]
        skuid = json_data["product"]["id"]
        title = json_data["product"]["title"]
        brand = json_data["product"]["brand"]
        breadlist = json_data["product"]["categoryFullPath"].replace('>', '/')
        color = json_data["product"]["color"]
        cur_price = float(
            str(json_data["product"]["price"]["price"])[:-2] + '.' + str(json_data["product"]["price"]["price"])[-2:])
        ori_price = float(str(json_data["product"]["price"]["originalPrice"])[:-2] + '.' + str(
            json_data["product"]["price"]["originalPrice"])[-2:])
        sizeSelectorStock= json_data["translations"]["sizeSelectorStock"]
        if sizeSelectorStock == 'Stock':
            oversold_all = False
        else:
            oversold_all = True
        description = [json_data["product"]["description"]]

        imgs = []
        images = json_data["product"]["images"]
        for image in images:
            imgs.append(image["url"])

        specs = []
        variants = json_data["product"]["sizes"]
        for variant in variants:
            spec = {
                'spec': color + ' / ' + variant["producerSize"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not variant["isLastItem"]
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

    execute('scrapy crawl miinto:goods_all_list'.split(' '))
