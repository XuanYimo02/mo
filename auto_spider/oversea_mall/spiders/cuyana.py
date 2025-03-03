# -*- coding: utf-8 -*-
# @Time : 2024-03-27 12:01
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
    name = 'cuyana:goods_all_list'
    platform = "cuyana"
    task_id = 'cuyana'
    sch_task = 'cuyana-task'
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
        "DOWNLOAD_DELAY": 1,
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
        url = 'https://cuyana.com/collections/shop?page=1'
        page = 1
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
        url = f'https://cuyana.com/collections/shop?page={page}'
        yield scrapy.Request(
            url=url,
            dont_filter=True,
            callback=self.parse_list,
            meta={'page': page}
        )
        div_list = response.xpath(
            '//*[@id="shopify-section-template--21636120478011__42ca4c3e-c9ac-4e99-bf44-2db531506029"]/section/div[3]/div[3]/div/div[1]/div/div').extract()
        if len(div_list):
            page += 1
            next_url = f'https://cuyana.com/collections/shop?page={page}'
            yield scrapy.Request(
                url=next_url,
                dont_filter=True,
                callback=self.parse_home,
                meta={'page': page},
            )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """

        div_list = response.xpath(
            '//*[@id="shopify-section-template--21636120478011__42ca4c3e-c9ac-4e99-bf44-2db531506029"]/section/div[3]/div[3]/div/div/div/div')

        if len(div_list):
            for div in div_list:
                if not ((div.xpath('./@class').extract()[
                             0] == "ColumnBlock col-12 col-md-12 offset-md-0  Grid__ContentCell") or (
                                div.xpath('./@class').extract()[
                                    0] == "ColumnBlock col-12 col-md-6 offset-md-0  Grid__ContentCell")):
                    detail_url = 'https://cuyana.com' + div.xpath('./div/div/div[1]/a[1]/@href').extract()[0]

                    yield scrapy.Request(
                        url=detail_url,
                        dont_filter=True,
                        callback=self.parse_detail,
                    )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """

        pattern = r'<script type="application/json" data-product-json>\n  {\n    "product":(.*?),\n    "configurator":'
        data_start = response.text
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        variants = json_data['variants']
        color_list = []
        for variant in variants:
            if variant['option1'] not in color_list:
                id = variant['id']
                color_list.append(variant['option1'])
                detail_url = response.url.split('=')[0] + '=' + str(id)
                yield scrapy.Request(
                    url=detail_url,
                    dont_filter=True,
                    callback=self.parse_de_detail,
                    meta={'color':variant['option1']}
                )


    async def parse_de_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script type="application/json" data-product-json>\n  {\n    "product":(.*?),\n    "configurator":'
        data_start = response.text
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data['id']
        skuid = response.url.split('=')[-1]
        title = json_data['title']
        cur_price = float(f"{str(json_data['price'])[:-2]}.{str(json_data['price'])[-2:]}")
        ori_price = float(f"{str(json_data['price'])[:-2]}.{str(json_data['price'])[-2:]}")
        oversold_all = not json_data['available']
        brand = self.platform
        category = f"Shop / {json_data['type']}"

        imgs = []
        imgs_list = response.xpath('//*[@id="shopify-section-template--18225671274811__main"]/section/div[2]/div[1]/div[1]/div/a')
        for img in imgs_list:
            image = "https:" + img.xpath('./img/@src').extract()[0]
            image = image.split('160x.jpg')[0]+'1000x.jpg'+image.split('160x.jpg')[1]
            imgs.append(image)

        description = []
        description_data = json_data["description"]
        pattern = r'>(.*?)<'

        clean_text = re.findall(pattern, description_data.replace('\n', ''))
        if clean_text != [] and clean_text != ['']:
            for clean in clean_text:
                if clean.replace(' ', '').replace('\r', '') != '':
                    description.append(clean)
        else:
            description = [description_data]

        specs = []
        variants = json_data["variants"]
        for variant in variants:
            if variant['option1'] == response.meta['color']:
                spec = {
                    'spec': variant['title'],
                    'price': cur_price,
                    'origPrice': ori_price,
                    'priceUnit': "$",
                    'oversold': not variant['available']
                }
                specs.append(spec)

        # oss_imgs = imgs
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        try:
            pic_url = oss_imgs[0]
        except:
            pic_url = ''
        try:
            orig_main_pic = imgs[0]
        except:
            orig_main_pic = ''
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
            "pic_url": pic_url,
            "orig_imgs": imgs,
            "orig_main_pic": orig_main_pic,
            "detail_url": response.url,
            "brand_name": brand,
            "category_info": category,
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

    execute('scrapy crawl cuyana:goods_all_list'.split(' '))
