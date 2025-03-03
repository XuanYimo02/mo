# -*- coding: utf-8 -*-
# @Time : 2024-04-08 16:19
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
from oversea_mall.auto_parse_class import AutoParse

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


class GoodsAllListSpider(DmSpider, AutoParse):
    name = 'bluebella:goods_all_list'
    platform = "bluebella"
    task_id = 'bluebella'
    sch_task = 'bluebella-task'
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
            'https://www.bluebella.us/collections/our-bestsellers?page=1',
            'https://www.bluebella.us/collections/swimwear?page=1',
            'https://www.bluebella.us/collections/lingerie?page=1',
            'https://www.bluebella.us/collections/lingerie-sets?page=1',
            'https://www.bluebella.us/collections/provocative-lingerie?page=1',
            'https://www.bluebella.us/collections/nightwear?page=1',
            'https://www.bluebella.us/collections/hosiery?page=1',
            'https://www.bluebella.us/collections/underwear-as-outerwear?page=1',
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
        div_list = response.xpath('//*[@id="shopify-section-collection"]/div/div[2]/section/div')
        for div in div_list:
            try:
                url = 'https://www.bluebella.us' + div.xpath('./figure/div/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        if len(div_list) > 1:
            page += 1
            url = response.url.split('?')[0] + '?page=%d' % page
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page}
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
        global cur_price, ori_price
        pattern = r'productId: "(\d+?)",'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        itemid = result.group(1)
        skuid = result.group(1)

        pattern = r'Name: "(.*?)",'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        title = result.group(1).replace('\\', '')

        pattern = r'"productCategory":"(.*?)",'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        breadlist = response.xpath('//*[@id="shopify-section-product"]/div[1]/div[1]/div/div/nav/a[2]/text()').extract()[0] + ' / ' + result.group(1)

        pattern = r'window.KlarnaThemeGlobals.productVariants=(.*?);window.KlarnaThemeGlobals.documentCopy'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        specs_data = json.loads(result.group(1))

        pattern = r'sswApp.product=(.*?);sswApp.themeNames'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        description_data = json.loads(result.group(1))


        description = []
        description_data = description_data["description"]
        pattern = r'>(.*?)<'

        clean_text = re.findall(pattern, description_data.replace('\n', ''))
        if clean_text != [] and clean_text != ['']:
            for clean in clean_text:
                if clean.replace(' ', '').replace('\r', '') != '':
                    description.append(clean)
        else:
            description = [description_data]

        imgs = []
        li_list = response.xpath('//*[@id="ProductGalleryMain-"]/ul/li')
        for li in li_list:
            url = ''
            try:
                url = 'https:' + li.xpath('./div/img/@src').extract()[0].split('1x1')[0] + '1080x' + \
                      li.xpath('./div/img/@src').extract()[0].split('1x1')[1]
            except:
                pass
            if url != '':
                imgs.append(url)
        specs = []
        oversold_all = True
        for specs_list in specs_data:
            price = float(str(specs_list['price'])[:-2] + '.' + str(specs_list['price'])[-2:])
            if specs_list['available']:
                oversold_all = False
            if specs_list['compare_at_price'] == None:
                origPrice = price
            else:
                origPrice = float(
                    str(specs_list['compare_at_price'])[:-2] + '.' + str(specs_list['compare_at_price'])[-2:])
            cur_price = price
            ori_price = origPrice
            spec = {
                "spec": specs_list['title'],
                "price": price,
                "origPrice": origPrice,
                "priceUnit": "$",
                "oversold": not specs_list['available']
            }
            specs.append(spec)

        # oss_imgs = imgs
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
            "brand_name": self.platform,
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

    execute('scrapy crawl bluebella:goods_all_list'.split(' '))
