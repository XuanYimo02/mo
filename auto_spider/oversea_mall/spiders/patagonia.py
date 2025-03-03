# -*- coding: utf-8 -*-
# @Time : 2024-05-13 16:53
# @Author : Mo

import logging
import os
import sys

import jsonpath

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
    name = 'patagonia:goods_all_list'
    platform = "patagonia"
    task_id = 'patagonia'
    sch_task = 'patagonia-task'
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
            'https://www.patagonia.com/shop/collections?page=30',
            'https://www.patagonia.com/shop/womens?page=30',
            'https://www.patagonia.com/shop/mens?page=30',
            'https://www.patagonia.com/shop/kids-baby?page=30',
            'https://www.patagonia.com/shop/gear?page=30',
            'https://www.patagonia.com/shop/web-specials?page=30',
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
        div_list = response.xpath('//*[@id="product-search-results"]/div[3]/div/div')
        for div in div_list:
            try:
                url = 'https://www.patagonia.com' + div.xpath('./div/div/div/div/div[1]/div[1]/div[2]/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script type="application/ld\+json" id="product-schema">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        color_list = json_data["color"]
        for color in color_list:
            url = response.url.split('color=')[0] + f'color={color}'
            yield scrapy.Request(
                url=url,
                callback=self.parse_item_detail,
                meta={'color': color}
            )

    async def parse_item_detail(self, response, **kwargs):
        global colors
        meta = response.meta
        description = []
        pattern = r'<script type="application/ld\+json" id="product-schema">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        descriptions = json_data["description"]
        if descriptions:
            descriptions = Selector(text=descriptions)
            descriptions = descriptions.xpath("//text()").extract()
            for des in descriptions:
                des = filter_html_label(des)
                if des:
                    description.append(des)
        meta['description'] = description

        imgs = []
        li_list = response.xpath('/html/body/main/section/div[2]/section/div[2]/ul/li')
        for li in li_list:
            try:
                image = li.xpath('./div/div[1]/div/picture/source/@srcset').extract()[0].split('512w')[0]
                if ',' in image:
                    image = image.split(',')[-1]
                imgs.append(image)
            except:
                pass
        meta['imgs'] = imgs

        pattern = r'"Primary Category":"(.*?)",'
        result = re.search(pattern, data_start)
        meta['breadlist'] = result.group(1)
        meta['ori_url'] = response.url

        pattern = r'<script type="application/ld\+json" id="product-schema">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        color_list = json_data["color"]
        pid = response.url.split('.html')[0].split('/')[-1]
        for color in color_list:
            if color == color_list[0]:
                colors = color
            else:
                colors += '|' + color
        params = {
            "pid": f"{pid}",
            f"dwvar_{pid}_color": f"{meta['color']}",
            "colors": f"{colors}",
            "storeID": "null"
        }
        url = "https://www.patagonia.com/on/demandware.store/Sites-patagonia-us-Site/en_US/Product-VariationAttributes?" + urlencode(
            params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_detail_api,
            meta=meta
        )

    async def parse_detail_api(self, response, **kwargs):
        try:
            meta = response.meta
            info = response.json()
            product_info = info['product']
            itemid = product_info['id']
            skuid = product_info['id'] + product_info["selectedColor"]["colorCode"]
            title = product_info.get('productName')
            brand = product_info.get('brand')
            if brand == None:
                brand = self.platform
            oversold = True
            colorCode = product_info["selectedColor"]["colorCode"]
            cur_price = product_info["colorPrice"][colorCode]['price']['sales']['value']
            if product_info["colorPrice"][colorCode]['price']['list'] == None:
                ori_price = cur_price
            else:
                ori_price = product_info["colorPrice"][colorCode]['price']['list']['value']

            specs = []
            values = product_info["variationAttributes"][1]["values"]
            for value in values:
                try:
                    if value["inStock"] == True:
                        oversold = False
                    colorText = product_info["selectedColor"]["colorText"]
                    spec = {
                        'spec': colorText + ' / ' + value["value"],
                        "price": cur_price,
                        "origPrice": ori_price,
                        "priceUnit": "$",
                        "oversold": not value["inStock"]
                    }
                    specs.append(spec)
                except:
                    pass

            imgs = meta['imgs']
            oss_imgs = get_oss_imgs(self.platform, imgs)
            await download_imgs(self.platform, imgs, skuid)
            item = {
                "platform": self.platform,
                "itemid": itemid,
                "skuid": skuid,
                "title": title,
                "description": meta['description'],
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
                "category_info": meta['breadlist'],
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

    execute('scrapy crawl patagonia:goods_all_list'.split(' '))
