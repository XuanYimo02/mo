# -*- coding: utf-8 -*-
# @Time : 2024-05-09 10:47
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
    num = 0
    name = 'bootbarn:goods_all_list'
    platform = "bootbarn"
    task_id = 'bootbarn'
    sch_task = 'bootbarn-task'
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
            'https://www.bootbarn.com/mens/boots-shoes/mens-boots-shoes/?&start=0&format=ajax',
            'https://www.bootbarn.com/workwear/work-boots/mens-work-boots/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/hats/mens-hats/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/shirts/mens-shirts/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/outerwear/all-mens-outerwear/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/bottoms/mens-bottoms/?&start=0&format=ajax',
            'https://www.bootbarn.com/workwear/work-clothing/mens-workwear/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/accessories/mens-belts-belt-buckles/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/accessories/mens-accessories/?&start=0&format=ajax',
            'https://www.bootbarn.com/mens/boots-shoes/mens-hiking-boots/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/boots-shoes/womens-boots-shoes/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/hats/womens-hats/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/bottoms-dresses/womens-dresses-skirts/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/shirts/all-womens-shirts/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/bottoms-dresses/womens-jeans-pants/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/outerwear/all-womens-outerwear/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/accessories/womens-accessories/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/accessories/womens-belts-buckles/?&start=0&format=ajax',
            'https://www.bootbarn.com/womens/boots-shoes/womens-outdoor-boots/?&start=0&format=ajax',
            'https://www.bootbarn.com/workwear/womens-work-boots-clothing/womens-workwear/?&start=0&format=ajax',
            'https://www.bootbarn.com/workwear/womens-work-boots-clothing/womens-work-boots-shoes/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/boots-shoes/boys-boots/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/boots-shoes/girls-boots/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/girls-clothing/girls-clothing/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/boys-clothing/boys-clothing/?&start=0&format=ajax',
            'https://www.bootbarn.com/featured/featured/go-texan-day/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/toys-accessories/kids-accessories/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/toys-accessories/kids-hats/?&start=0&format=ajax',
            'https://www.bootbarn.com/kids/toys-accessories/kids-toys/?&start=0&format=ajax',
            'https://www.bootbarn.com/featured/collections/backpacks/?&start=0&format=ajax',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': 0}
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        meta = response.meta
        page = meta['page']
        li_list = response.xpath('//*[@id="search-result-items"]/li')
        for li in li_list:
            url = li.xpath('./div/div[1]/a/@href').extract()[0]
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
            )

        if len(li_list):
            page += 1
            meta['page'] = page
            url = response.url.split('&')[0] + f'&start={48*page}&format=ajax'
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta=meta
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
        meta = response.meta
        meta['ori_url'] = response.url
        detail_url_post = 'https://www.bootbarn.com/on/demandware.store/Sites-bootbarn_us-Site/default/Product-GetVariationAttributes'
        pid = response.url.split('.html')[0].split('/')[-1]
        colorid = response.url.split('color=')[-1]

        pattern = r'pageContext = (.*?);</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        meta['title'] = json_data["title"]
        meta['brand'] = json_data["options"]["GoogleTagManager"]["DataLayerCacheForGoogleAnalytics4"]["items"]["item_brand"]
        item_category = json_data["options"]["GoogleTagManager"]["DataLayerCacheForGoogleAnalytics4"]["items"]["item_category"]
        item_category2 = json_data["options"]["GoogleTagManager"]["DataLayerCacheForGoogleAnalytics4"]["items"]["item_category2"]
        # item_category3 = json_data["options"]["GoogleTagManager"]["DataLayerCacheForGoogleAnalytics4"]["items"]["item_category3"]
        meta['breadlist'] = item_category + ' / ' + item_category2
        meta['itemid'] = pid + colorid
        meta['skuid'] = pid + colorid

        try:
            meta['ori_price'] = float(response.xpath('//*[@id="pdp-details"]/div[2]/div[1]/div[1]/div/strong/text()').extract()[0].split('$')[1].replace(',', ''))
            meta['cur_price'] = float(response.xpath('//*[@id="pdp-details"]/div[2]/div[1]/div[1]/span[1]/strong/text()').extract()[0].split('$')[1].replace(',', ''))
        except:
            meta['ori_price'] = float(response.xpath('//*[@id="pdpMain"]/div[1]/div[2]/div[1]/div/span[1]/strong/text()').extract()[0].split('$')[1].replace(',', ''))
            meta['cur_price'] = meta['ori_price']

        meta['description'] = []
        li_list = response.xpath('//*[@id="pdp-details"]/div[4]/div/div/div/div/ul/li')
        if len(li_list) == 0:
            li_list = response.xpath('//*[@id="pdp-details"]/div[5]/div/div/div/div/ul/li')
        for li in li_list:
            meta['description'].append(li.xpath('./text()').extract()[0])

        meta['imgs'] = []
        images = response.xpath('//*[@id="thumbnails"]/div/div')
        images = response.xpath('//*[@id="pdpMain"]/div[1]/div[3]/div/div[2]/div[1]/div/div/div/div/div')

        for image in images:
            img = image.xpath('./a/@href').extract()[0]
            meta['imgs'].append(img)

        data = {
            "Quantity": "1",
            "cartAction": "update",
            "pid": str(pid),
            f"dwvar_{pid}_color": str(colorid)
        }
        # data = json.dumps(data, separators=(',', ':'))
        yield scrapy.FormRequest(
            url=detail_url_post,
            formdata=data,
            callback=self.parse_detail_post,
            meta=meta
        )

    async def parse_detail_post(self, response, **kwargs):
        try:
            meta = response.meta
            info = response.json()

            oversold = True
            specs = []
            skus = info["variations"][1]["values"] if info["variations"][1]["values"] else []
            for sku in skus:
                color = info["selected"]["color"]["displayValue"]
                spec = sku.get('text')
                sku_cur_price = meta['cur_price']
                sku_ori_price = meta['ori_price']
                sku_oversold = False
                sku_ability = sku.get('selectable')
                if sku_ability == False:
                    sku_oversold = True
                if sku_oversold == False:
                    oversold = False
                if spec:
                    specs_item = {
                        "spec": color + ' / ' + spec,
                        "price": sku_cur_price,
                        "origPrice": sku_ori_price,
                        "priceUnit": "$",
                        "oversold": sku_oversold,
                    }
                    specs.append(specs_item)

            imgs = meta['imgs']
            oss_imgs = get_oss_imgs(self.platform, imgs)
            await download_imgs(self.platform, imgs, meta['skuid'])
            item = {
                "platform": self.platform,
                "itemid": meta['itemid'],
                "skuid": meta['skuid'],
                "title": meta['title'],
                "description": meta['description'],
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

    execute('scrapy crawl bootbarn:goods_all_list'.split(' '))
