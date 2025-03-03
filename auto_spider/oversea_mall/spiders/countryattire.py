# -*- coding: utf-8 -*-
# @Time : 2024-04-18 14:58
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
    name = 'countryattire:goods_all_list'
    platform = "countryattire"
    task_id = 'countryattire'
    sch_task = 'countryattire-task'
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
        page = 1
        urls = [
            'https://www.brandalley.co.uk/women/clothing.html?p=1',
            'https://www.brandalley.co.uk/women/shoes.html?p=1',
            'https://www.brandalley.co.uk/women/lingerie.html?p=1',
            'https://www.brandalley.co.uk/women/accessories-handbags.html?p=1',
            'https://www.brandalley.co.uk/men/clothing.html?p=1',
            'https://www.brandalley.co.uk/men/shoes.html?p=1',
            'https://www.brandalley.co.uk/men/accessories.html?p=1',
            'https://www.brandalley.co.uk/home/bed-bath.html?p=1',
            'https://www.brandalley.co.uk/home/kitchen-dining.html?p=1',
            'https://www.brandalley.co.uk/home/home-accessories.html?p=1',
            'https://www.brandalley.co.uk/home/living-room-furniture.html?p=1',
            'https://www.brandalley.co.uk/home/dining-room-furniture.html?p=1',
            'https://www.brandalley.co.uk/home/kitchen-furniture.html?p=1',
            'https://www.brandalley.co.uk/kids/clothing.html?p=1',
            'https://www.brandalley.co.uk/kids/shoes.html?p=1',
            'https://www.brandalley.co.uk/kids/games-toys.html?p=1',
            'https://www.brandalley.co.uk/outdoor/garden-furniture.html?p=1',
            'https://www.brandalley.co.uk/outdoor/outdoor-cooking-heating.html?p=1',
            'https://www.brandalley.co.uk/outdoor/outdoor-lighting.html?p=1',
            'https://www.brandalley.co.uk/outdoor/garden-buildings-storage.html?p=1',
            'https://www.brandalley.co.uk/outdoor/outdoor-accessories.html?p=1',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page, 'l': 64}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        l = response.meta['l']
        li_list = response.xpath('//*[@id="root-wrapper"]/div[1]/div/div[2]/div[1]/div/div[2]/div[10]/div[3]/ul/li')
        for li in li_list:
            url = li.xpath('./div[1]/a[1]/@href').extract()[0]
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        if len(li_list) and (not (l == len(li_list) and l != 64)):
            page += 1
            url = response.url.split('?')[0] + '?p=%d' % page
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page, 'l': len(li_list)}
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
        pattern = r'window.universal_variable.product = (.*?);                        window.universal_variable.basket'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data['id']
        skuid = json_data['sku']
        title = json_data['name']
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

        breadlist = f"{json_data['domain']} / {json_data['category']} / {json_data['subcategory']}"
        colour = json_data['colour']
        availability = json_data['availability']
        brand = json_data['brand']

        imgs = []
        li_list = response.xpath('//*[@id="root-wrapper"]/div[1]/div/div[2]/div[1]/div/div[3]/div[3]/div[1]/div/div[2]/div/ul/li')
        for li in li_list:
            url = li.xpath('./a/@href').extract()[0]
            imgs.append(url)

        url = f'https://www.brandalley.co.uk/configurabledisplay/ajax/getjs?productid={itemid}'
        yield scrapy.Request(
            url=url,
            callback=self.parse_item_detail,
            meta={
                'itemid': itemid,
                'skuid': skuid,
                'title': title,
                'description': description,
                'breadlist': breadlist,
                'colour': colour,
                'availability': availability,
                'brand': brand,
                'imgs': imgs,
                'response_url': response.url,
            }
        )


    async def parse_item_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        options = response.json()["attributes"]["177"]["options"]

        if response.meta['availability'] == 'Yes':
            oversold_all = False
        else:
            oversold_all = True

        cur_price = float(response.json()['basePrice'])
        ori_price = float(response.json()['oldPrice'])

        specs = []
        for option in options:
            size = option['label'].split(' - ')[0]
            if option['data_qty']:
                oversold = False
            else:
                oversold = True
            spec = {
                'spec': f'{response.meta["colour"]} / {size}',
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "￡",
                "oversold": oversold
            }
            specs.append(spec)

        skuid =response.meta['skuid']
        imgs = response.meta['imgs']
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": response.meta['itemid'],
            "skuid": skuid,
            "title": response.meta['title'],
            "price": cur_price,
            "orig_price": ori_price,
            "price_unit": "￡",
            "prices": {"UK": {"p": cur_price, "o": ori_price, 'u': "￡"}},
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": response.meta['response_url'],
            "brand_name": response.meta['brand'],
            "category_info": response.meta['breadlist'],
            "specs": specs,
            "description": response.meta['description'],
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

    execute('scrapy crawl countryattire:goods_all_list'.split(' '))
