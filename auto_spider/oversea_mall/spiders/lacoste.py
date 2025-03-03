# -*- coding: utf-8 -*-
# @Time : 2024-05-28 17:58
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
    num = 0
    name = 'lacoste:goods_all_list'
    platform = "lacoste"
    task_id = 'lacoste'
    sch_task = 'lacoste-task'
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
            'https://www.lacoste.com/us/lacoste/men/clothing/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/women/clothing/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/women/shoes/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/discover/sport-collections/women/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/women/bags-leather-goods/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/women/accessories/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/men/shoes/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/discover/sport-collections/men/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/men/bags-leather-goods/?sortBy=lc_t2s_rank4&page=1',
            'https://www.lacoste.com/us/lacoste/men/accessories/?sortBy=lc_t2s_rank4&page=1',
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
        div_list = response.xpath('/html/body/main/section/div[2]/div[2]/div/div[1]/div')
        if len(div_list) == 0:
            div_list = response.xpath('/html/body/main/section/div[3]/div[2]/div/div[1]/div')
        for div in div_list:
            try:
                url = div.xpath('./div/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        if len(div_list):
            page += 1
            url = response.url.split('&')[0] + '&page=%d' % page
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
        data_start = response.text.replace('\n', '')
        pattern = r'"ecommerce":(.*?)}\);'
        result = re.search(pattern, data_start)
        detail_data = json.loads(result.group(1))

        meta['itemid'] = detail_data["items"][0]["item_id"]
        meta['skuid'] = detail_data["items"][0]["item_id"]
        meta['title'] = detail_data["items"][0]["item_name"]
        meta['cur_price'] = detail_data["items"][0]["price"]
        meta['ori_price'] = detail_data["items"][0]["full_price"]
        meta['breadlist'] = detail_data["items"][0]["item_category3"] + ' / ' + detail_data["items"][0]["item_category4"]

        size_availability = detail_data["items"][0]["size_availability"]
        if size_availability:
            meta['oversold_all'] = False
        else:
            meta['oversold_all'] = True

        pattern = r'</section><script type="application/ld\+json">(.*?)</script>'
        result = re.search(pattern, data_start)
        description_data = json.loads(result.group(1))
        try:
            meta['description'] = [description_data["description"]]
            meta['brand'] = description_data["brand"]
        except:
            meta['description'] = []
            meta['brand'] = description_data["name"]

        imgs = []
        pattern = r'"gallery":(.*?)}\);'
        result = re.search(pattern, data_start)
        imgs_data = json.loads(result.group(1).replace('&quot;', '"'))
        images = imgs_data["images"]
        for image in images:
            img = 'https:' + image["desktopUrl"]
            imgs.append(img)
        meta['imgs'] = imgs

        productIds = response.url.split('.html')[0].split('/')[-1]
        params = {
            "type": "variations",
            "productIds": productIds,
            "full": "true",
            "format": "json"
        }
        url = "https://www.lacoste.com/on/demandware.store/Sites-FlagShip-Site/en_US/Product-Api?" + urlencode(params)
        meta['ori_url'] = response.url
        yield scrapy.Request(
            url=url,
            callback=self.parse_detail_js,
            meta=meta
        )


    async def parse_detail_js(self, response, **kwargs):
        meta = response.meta
        color = response.json()["data"][0]["variations"]["color"]["list"][0]["label"]
        size_list = response.json()["data"][0]["variations"]["size"]["list"]
        specs = []
        for li in size_list:
            spec = {
                'spec': color + ' / ' + li["label"],
                "price": meta['cur_price'],
                "origPrice": meta['ori_price'],
                "priceUnit": "$",
                "oversold": li["unavailable"]
            }
            specs.append(spec)

        imgs = meta['imgs']
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, meta['skuid'])
        item = {
            "platform": self.platform,
            "itemid": meta['itemid'],
            "skuid": meta['skuid'],
            "title": meta['title'],
            "price": meta['cur_price'],
            "orig_price": meta['ori_price'],
            "price_unit": "$",
            "prices": {"US": {"p": meta['cur_price'], "o": meta['ori_price'], 'u': "$"}},
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": meta['ori_url'],
            "brand_name": meta['brand'],
            "category_info": meta['breadlist'],
            "specs": specs,
            "description": meta['description'],
            "insert_time": get_now_datetime(),
            "online": True,
            "oversold": meta['oversold_all'],
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

    execute('scrapy crawl lacoste:goods_all_list'.split(' '))
