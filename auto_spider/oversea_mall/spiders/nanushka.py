# -*- coding: utf-8 -*-
# @Time : 2024-05-11 17:26
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
    name = 'nanushka:goods_all_list'
    platform = "nanushka"
    task_id = 'nanushka'
    sch_task = 'nanushka-task'
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
            'https://www.nanushka.com/collections/women-all-products?page=1',
            'https://www.nanushka.com/collections/men-all-products?page=1',
            'https://www.nanushka.com/collections/all-accessories?page=1'
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
        li_list = response.xpath('//*[@id="product-grid"]/li')
        for li in li_list:
            try:
                url = 'https://www.nanushka.com' + li.xpath('./product-card/div/div[1]/div/div/product-card-gallery/slider-component/ul/li[1]/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        if len(li_list):
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
        meta = response.meta
        meta['ori_url'] = response.url
        detail_url_js = response.url.split('?')[0] + '.js'
        yield scrapy.Request(
            url=detail_url_js,
            callback=self.parse_detail_js,
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
            ori_price = float(info.get('compare_at_price')) / 100 if info.get('compare_at_price') and info.get('compare_at_price') != 0 else cur_price
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
                sku_ori_price = float(sku.get('compare_at_price')) / 100 if sku.get('compare_at_price') and sku.get('compare_at_price') != 0 else sku_cur_price
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

            # oss_imgs = imgs
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

    execute('scrapy crawl nanushka:goods_all_list'.split(' '))
