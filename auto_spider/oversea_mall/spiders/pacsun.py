# -*- coding: utf-8 -*-
# @Time : 2024-05-09 10:24
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
    number = 0
    name = 'pacsun:goods_all_list'
    platform = "pacsun"
    task_id = 'pacsun'
    sch_task = 'pacsun-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        'DOWNLOAD_HANDLERS': {
            # 'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
            # 'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 3,
        'DOWNLOAD_TIMEOUT': 10,
        "LOG_LEVEL": "INFO",
        "EXIT_ENABLED": True,
        'LOG_FILE': log_file_path,
        'LOG_STDOUT': False,
        'REDIRECT_ENABLED': False
    }

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=1, i",
        "referer": "https://www.pacsun.com/womens/",
        "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
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
            'https://www.pacsun.com/womens/',
            'https://www.pacsun.com/mens/',
            'https://www.pacsun.com/kids/',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                headers=self.headers
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        params = {
            "cgid": "womens",
            "start": "0",
            "sz": "12",
            "selectedUrl": "https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Search-UpdateGrid?cgid=womens&start=0&sz=12"
        }
        url = "https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Search-UpdateGrid?" + urlencode(params)
        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            headers=self.headers,
            meta={'page': 0}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']

        div_list = response.xpath('/html/body/div[1]/div[2]/div')
        for div in div_list:
            try:
                url = 'https://www.pacsun.com' + div.xpath('./div/div/div[2]/div[2]/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    headers=self.headers,
                    dont_filter=True
                )
            except:
                pass

        if len(div_list):
            page += 1
            meta['page'] = page
            params = {
                "cgid": "womens",
                "start": f"{12*page}",
                "sz": "12",
                "selectedUrl": f"https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Search-UpdateGrid?cgid=womens&start={12*page}&sz=12"
            }
            url = "https://www.pacsun.com/on/demandware.store/Sites-pacsun-Site/default/Search-UpdateGrid?" + urlencode(params)
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
        """
        pattern = r'"product": (.*?),    "resources":'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        if '&' in response.url:
            color_values = json_data["variationAttributes"][1]["values"]
            for color_value in color_values:
                color = color_value['value']
                url = response.url.split('color=')[0] + f'color={color}&' + response.url.split('&')[-1]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail_color,
                    headers=self.headers,
                    meta={'color': color},
                    dont_filter=True
                )
        else:
            color = json_data["variationAttributes"][1]["values"][0]["value"]
            yield scrapy.Request(
                url=response.url,
                callback=self.parse_detail_color,
                headers=self.headers,
                meta={'color': color},
                dont_filter=True
            )


    async def parse_detail_color(self, response, **kwargs):
        global sku_oversold, breadlist
        try:
            pattern = r'"product": (.*?),    "resources":'
            data_start = response.text.replace('\n', '')
            result = re.search(pattern, data_start)
            detail_json_data = json.loads(result.group(1))

            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            data_start = response.text.replace('\n', '')
            result = re.search(pattern, data_start)
            json_data = json.loads(result.group(1))

            color_values = detail_json_data["variationAttributes"][1]["values"]
            color = response.meta['color']
            itemid = json_data["productGroupID"] + color
            skuid = json_data["productGroupID"] + color
            title = json_data["name"]
            brand = json_data["brand"]["name"]
            description = []
            descriptions = json_data["description"]
            if descriptions:
                descriptions = Selector(text=descriptions)
                descriptions = descriptions.xpath("//text()").extract()
                for des in descriptions:
                    des = filter_html_label(des)
                    if des:
                        description.append(des)

            imgs = []
            hasVariants = json_data["hasVariant"]
            for hasVariant in hasVariants:
                if color == hasVariant['color']:
                    image = hasVariant['image']
                    for img in image:
                        if not img.startswith('http'):
                            img = 'https:' + img
                        if img not in imgs:
                            imgs.append(img)

            oversold = False
            ability = detail_json_data["variationAttributes"][1]["price"][0]["selectable"]
            if ability == False:
                oversold = True
            ori_price = detail_json_data["variationAttributes"][1]["price"][0]["price"]
            cur_price = detail_json_data["variationAttributes"][1]["price"][0]["salesPrice"]

            specs = []
            hasVariants = json_data["hasVariant"]
            for hasVariant in hasVariants:
                if color == hasVariant['color']:
                    size = hasVariant["size"]
                    size_values = detail_json_data["variationAttributes"][0]["values"]
                    for value in size_values:
                        if value['value'] == size:
                            size = value['displayValue']
                            sku_oversold = not value["selectable"]
                    specs_item = {
                        "spec": color + ' / ' + size,
                        "price": cur_price,
                        "origPrice": ori_price,
                        "priceUnit": "$",
                        "oversold": sku_oversold,
                    }
                    specs.append(specs_item)

            pattern = r'</script>    <script type="application/ld\+json">(.*?)</script></head>'
            data_start = response.text.replace('\n', '')
            result = re.search(pattern, data_start)
            json_data = json.loads(result.group(1))
            itemListElement = json_data["itemListElement"]
            for itemElement in itemListElement:
                if itemElement == itemListElement[0]:
                    breadlist = itemElement["name"]
                else:
                    breadlist += ' / ' + itemElement["name"]

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
                "detail_url": response.url,
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

    execute('scrapy crawl pacsun:goods_all_list'.split(' '))
