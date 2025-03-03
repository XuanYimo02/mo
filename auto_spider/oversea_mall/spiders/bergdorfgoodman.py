# -*- coding: utf-8 -*-
# @Time : 2024-05-21 15:06
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
    name = 'bergdorfgoodman:goods_all_list'
    platform = "bergdorfgoodman"
    task_id = 'bergdorfgoodman'
    sch_task = 'bergdorfgoodman-task'
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
            'https://www.bergdorfgoodman.com/c/shoes-cat428606?page=1',
            'https://www.bergdorfgoodman.com/c/sale-cat441307?page=1',
            'https://www.bergdorfgoodman.com/c/womens-clothing-cat441206?page=1',
            'https://www.bergdorfgoodman.com/c/handbags-cat428607?page=1',
            'https://www.bergdorfgoodman.com/c/accessories-cat441106?page=1',
            'https://www.bergdorfgoodman.com/c/beauty-cat478300?page=1',
            'https://www.bergdorfgoodman.com/c/men-clothing-cat521724?page=1',
            'https://www.bergdorfgoodman.com/c/kids-baby-cat369100?page=1',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': 1}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        if page == 1:
            div_list = response.xpath('//*[@id="mainContent"]/div[2]/div/div[3]/div[1]/div/div')
        else:
            div_list = response.xpath('//*[@id="mainContent"]/div[2]/div/div[3]/div[1]/div')

        for div in div_list:
            try:
                url = 'https://www.bergdorfgoodman.com' + div.xpath('./a/@href').extract()[0]
                # url = 'https://www.bergdorfgoodman.com/p/valentino-garavani-rockstud-resort-thong-slide-sandals-prod186060028?childItemId=BGX6KHB_&navpath=cat000000_cat200648_cat428606&page=1&position=110&uuid=PDP_PAGINATION_79fc7cc6ba46f6657508f0fe2102f94b_7bVFrvHjF3ySijj6mKCrqzugxCdELZgR_gzbIjsn.jsession'
                # url = 'https://www.bergdorfgoodman.com/p/cinq-a-sept-marta-cowl-neck-silk-camisole-prod177030056?childItemId=BGT4AAG_&navpath=cat000000_cat205700_cat441307&page=36&position=59&uuid=PDP_PAGINATION_59ea5e9398f6c70ff472c24e4276bd9e_OFkLiLFW9c6l9LtLkm5ydbwHiynTj3crfzae3GeG.jsession'
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

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
        global breadlist
        pattern = r'type="application/json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["ecm"]["ecmContent"]["headers"]["productId"]
        skuid = json_data["ecm"]["ecmContent"]["headers"]["productId"]
        title = json_data["chatData"]["title"]
        brand = json_data["chatData"]["product_brand"]

        categories = json_data["mobileNav"]["silos"][2]["categories"][0]["categories"]
        for category in categories:
            if json_data["config"]["customerSegment"]["targetedSilo"]["categoryId"] == category["catmanId"]:
                breadlist = category["name"]

        hierarchies = json_data["productCatalog"]["product"]["hierarchy"][0]
        for key,hierarchy in hierarchies.items():
            if key == 'level1':
                breadlist = hierarchy
            else:
                breadlist += ' / ' + hierarchy

        cur_price = float(json_data["productCatalog"]["product"]["price"]["retailPrice"])
        try:
            ori_price = float(json_data["productCatalog"]["product"]["price"]["adornments"][0]["price"])
        except:
            ori_price = cur_price
        available_sku_count = json_data["utag"]["product"]["productInfo"]["available_sku_count"]
        oversold_all = True
        if available_sku_count:
            oversold_all = False

        description = []
        try:
            descriptions = json_data["productCatalog"]["product"]["linkedData"]["description"]
            if descriptions:
                descriptions = Selector(text=descriptions)
                descriptions = descriptions.xpath("//text()").extract()
                for des in descriptions:
                    des = filter_html_label(des)
                    if des:
                        description.append(des)
        except:
            pass

        imgs = []
        try:
            try:
                values = json_data["productListPage"]["productCatalog"]["product"]["options"]["productOptions"][1]["values"]
            except:
                values = json_data["productListPage"]["productCatalog"]["product"]["options"]["productOptions"][0]["values"]
        except:
            return
        for value in values:
            try:
                imgs.append('https:' + value["media"]["main"]["dynamic"]["url"])
                alternates = value["media"]["alternate"]
                for key, alternate in alternates.items():
                    image_url = alternate["dynamic"]["url"]
                    imgs.append('https:' + image_url)
            except:
                pass

        if imgs == []:
            return

        specs = []
        try:
            variants = json_data["productCatalog"]["product"]["skus"]
            for variant in variants:
                spec = {
                    'spec': variant["color"]["name"] + ' / ' + variant["size"]["name"],
                    "price": cur_price,
                    "origPrice": ori_price,
                    "priceUnit": "$",
                    "oversold": not variant["inStock"]
                }
                specs.append(spec)
        except:
            offers = json_data["productListPage"]["productCatalog"]["product"]["linkedData"]["offers"]["offers"]
            for offer in offers:
                spec = {
                    'spec': offer["name"],
                    "price": cur_price,
                    "origPrice": ori_price,
                    "priceUnit": "$",
                    "oversold": not ('InStock' in offer["availability"])
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

    execute('scrapy crawl bergdorfgoodman:goods_all_list'.split(' '))
