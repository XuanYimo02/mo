# -*- coding: utf-8 -*-
# @Time : 2024-06-06 16:42
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
import jsonpath
from scrapy import Selector
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
    name = 'ysl:goods_all_list'
    platform = "ysl"
    task_id = 'ysl'
    sch_task = 'ysl-task'
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
            'https://www.ysl.com/en-us/shop-women/fine-jewelry',
            'https://www.ysl.com/en-us/shop-women/gifts-selection',
            'https://www.ysl.com/en-us/shop-women/resort',
            'https://www.ysl.com/en-us/shop-women/handbags/all-handbags',
            'https://www.ysl.com/en-us/shop-women/small-leather-goods/all-small-leather-goods',
            'https://www.ysl.com/en-us/shop-women/ready-to-wear/all-ready-to-wear',
            'https://www.ysl.com/en-us/shop-women/shoes/all-shoes',
            'https://www.ysl.com/en-us/shop-women/belts-and-belt-bags',
            'https://www.ysl.com/en-us/shop-women/accessories/all-accessories',
            'https://www.ysl.com/en-us/shop-women/sunglasses',
            'https://www.ysl.com/en-us/shop-women/jewelry/all-jewelry',
            'https://www.ysl.com/en-us/shop-men/ready-to-wear/all-ready-to-wear',
            'https://www.ysl.com/en-us/shop-men/shoes/all-shoes',
            'https://www.ysl.com/en-us/shop-men/bags/all-bags',
            'https://www.ysl.com/en-us/shop-men/small-leather-goods/all-small-leather-goods',
            'https://www.ysl.com/en-us/shop-men/belts',
            'https://www.ysl.com/en-us/shop-men/jewelry/all-jewelry',
            'https://www.ysl.com/en-us/shop-men/accessories/all-accessories',
            'https://www.ysl.com/en-us/shop-men/sunglasses',
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
        pattern = r'"productCategory":"(.*?)",'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        cgid = result.group(1)

        params = {
            "cgid": cgid,
            "prefn1": "akeneo_employeesSalesVisible",
            "prefv1": "false",
            "prefn2": "akeneo_markDownInto",
            "prefv2": "no_season",
            "prefn3": "countryInclusion",
            "prefv3": "US",
            "start": "0",
            "sz": "12"
        }
        url = "https://www.ysl.com/on/demandware.store/Sites-SLP-NOAM-Site/en_US/Search-UpdateGrid?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            meta={'page': 0, 'cgid': cgid}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        cgid = meta['cgid']

        li_list = response.xpath('//*[@id="tiles"]/li')
        for li in li_list:
            try:
                url = 'https://www.ysl.com' + li.xpath('./article/div/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers
                )
            except:
                pass

        # print(cgid, page, len(li_list))
        if len(li_list):
            page += 12
            meta['page'] = page
            meta['cgid'] = cgid
            params = {
                "cgid": cgid,
                "prefn1": "akeneo_employeesSalesVisible",
                "prefv1": "false",
                "prefn2": "akeneo_markDownInto",
                "prefv2": "no_season",
                "prefn3": "countryInclusion",
                "prefv3": "US",
                "start": page,
                "sz": "12"
            }
            url = "https://www.ysl.com/on/demandware.store/Sites-SLP-NOAM-Site/en_US/Search-UpdateGrid?" + urlencode(
                params)
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
        api eg:https://www.filippa-k.com/on/demandware.store/Sites-FilippaK-Site/en_US/Product-Variation?pid=30625-9947&quantity=1
        """
        meta = response.meta
        # 注意不同颜色间pid是否相同，如不同颜色pid相同，则detail_api_url需增加额外参数,默认同一detail_api_url除尺寸外，其余sku都选好了。
        pid = response.url.split('.html')[0].split('-')[-1]
        p_list = response.xpath('//*[@id="main-content"]/div/div/div[10]/div/div[2]/div/div/div[1]/div[1]/div[3]/div/div[1]/fieldset/div/p')
        for p in p_list:
            color = p.xpath('./label/span[2]/@data-attr-value').extract()[0]
            detail_api_url = f'https://www.ysl.com/on/demandware.store/Sites-SLP-NOAM-Site/en_US/Product-Variation?dwvar_{pid}_color={color}&pid={pid}&quantity=1'
            meta['ori_url'] = response.url
            yield scrapy.Request(
                url=detail_api_url,
                callback=self.parse_detail_api,
                meta=meta
            )

    async def parse_detail_api(self, response, **kwargs):
        # print(response.meta['ori_url'], response.json())
        # return

        meta = response.meta
        itemid = response.json()["product"]["id"]
        skuid = response.json()["product"]["id"]
        title = response.json()["product"]["productTitle"]
        breadlist = response.json()["product"]["primaryCategoryID"]
        brand = response.json()["product"]["brand"]
        description = []
        descriptions = response.json()["product"]["longDescription"] if response.json()["product"]["longDescription"] else ''
        if descriptions:
            descriptions = Selector(text=descriptions)
            descriptions = descriptions.xpath("//text()").extract()
            for des in descriptions:
                des = filter_html_label(des)
                if des:
                    description.append(des)
        descriptions = response.json()["product"]["shortDescription"] if response.json()["product"]["shortDescription"] else ''
        if descriptions:
            descriptions = Selector(text=descriptions)
            descriptions = descriptions.xpath("//text()").extract()
            for des in descriptions:
                des = filter_html_label(des)
                if des:
                    description.append(des)
        oversold_all = not response.json()["product"]["available"]
        cur_price = response.json()["product"]["price"]["sales"]["value"]
        ori_price = response.json()["product"]["price"]["sales"]["value"]

        specs = []
        color = response.json()["product"]["variationAttributes"][0]["selectedValue"]
        variants = response.json()["product"]["variationAttributes"][1]["values"]
        for variant in variants:
            spec = {
                'spec': color + ' / ' + variant["displayValueEnglish"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not variant["selectable"]
            }
            specs.append(spec)


        imgs = []
        image_list = response.json()["product"]["akeneoImages"]["packshot"]
        for image in image_list:
            img = image["large"]
            imgs.append(img)

        oss_imgs = get_oss_imgs(self.platform, imgs)
        # await download_imgs(self.platform, imgs, skuid)
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

    execute('scrapy crawl ysl:goods_all_list'.split(' '))
