# -*- coding: utf-8 -*-
# @Time : 2024-04-03 10:42
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
    name = 'minnetonkamoccasin:goods_all_list'
    platform = "minnetonkamoccasin"
    task_id = 'minnetonkamoccasin'
    sch_task = 'minnetonkamoccasin-task'
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
        'LOG_STDOUT':False,
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
            'https://www.minnetonkamoccasin.com/kids/styles',
            'https://www.minnetonkamoccasin.com/women/styles',
            'https://www.minnetonkamoccasin.com/men/styles',
            'https://www.minnetonkamoccasin.com/accessories/styles',
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_home,
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        url = response.url + '?&ajaxscroll=1&p=1'
        yield scrapy.Request(
            url=url,
            dont_filter=True,
            callback=self.parse_list,
            meta={'page': 1}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        global li_list
        page = response.meta['page']
        try:
            li_list = response.xpath('//*[@class="item product product-item"]')
        except:
            pass
        for li in li_list:
            url = li.xpath('./div/a/@href').extract()[0]
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_detail,
            )
        if len(li_list):
            page += 1
            url = response.url.split('?')[0] + f'?&ajaxscroll=1&p={page}'
            yield scrapy.Request(
                url=url,
                dont_filter=True,
                callback=self.parse_list,
                meta={'page': page}
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        global breadlist
        size_list=[]
        pattern = r'"Magento_Swatches/js/swatch-renderer": (.*?)        }    }</script><script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        try:
            json_data = json.loads(result.group(1))
        except:
            return

        pattern = r'"xnotif": (.*?)                                    }                         }                    }                   </script><script type="text/x-magento-init">'
        result = re.search(pattern, data_start)
        json_oversold = json.loads(result.group(1))

        itemid = json_data["jsonConfig"]["productId"]
        skuid = json_data["jsonConfig"]["productId"]
        title = response.xpath('//*[@class="page-title-wrapper product"]/h1/span/text()').extract()[0]
        brand = response.xpath('//*[@class="page-title-wrapper product"]/h1/span/text()').extract()[0]
        li_list = response.xpath('//*[@id="html-body"]/div[3]/div[2]/ul/li')
        for li in li_list[1:-1]:
            if li == li_list[1]:
                breadlist = li.xpath('./a/text()').extract()[0]
            else:
                breadlist += ' / ' + li.xpath('./a/text()').extract()[0]

        color_list = json_data["jsonConfig"]["attributes"]["92"]["options"]
        try:
            size_list = json_data["jsonConfig"]["attributes"]["176"]["options"]
        except:
            pass
        try:
            size_list = json_data["jsonConfig"]["attributes"]["175"]["options"]
        except:
            pass
        ori_price = json_data["jsonConfig"]["prices"]["oldPrice"]["amount"]
        cur_price = json_data["jsonConfig"]["prices"]["finalPrice"]["amount"]
        oversold_all = json_oversold["is_in_stock"]
        if oversold_all == 1:
            oversold_all = False
        else:
            oversold_all = True

        specs = []
        options = json_data["jsonConfig"]["optionPrices"]
        for (option_key, option_value) in options.items():
            for color_li in color_list:
                if option_key in color_li['products']:
                    color = color_li['label']
                    if size_list == []:
                        for oversold_dict in json_oversold.values():
                            try:
                                if oversold_dict['product_id'] == option_key:
                                    oversold = oversold_dict['is_in_stock']
                                    if oversold == 1:
                                        oversold = False
                                    else:
                                        oversold = True
                                    spec = {
                                        "spec": color,
                                        "price": option_value["finalPrice"]["amount"],
                                        "origPrice": option_value["oldPrice"]["amount"],
                                        "priceUnit": "$",
                                        "oversold": oversold,
                                    }
                                    specs.append(spec)
                            except:
                                pass
                    else:
                        for size_li in size_list:
                            if option_key in size_li['products']:
                                size = size_li['label']
                                for oversold_dict in json_oversold.values():
                                    try:
                                        if oversold_dict['product_id'] == option_key:
                                            oversold = oversold_dict['is_in_stock']
                                            if oversold == 1:
                                                oversold = False
                                            else:
                                                oversold = True
                                            spec = {
                                                "spec": f'{color} / {size}',
                                                "price": option_value["finalPrice"]["amount"],
                                                "origPrice": option_value["oldPrice"]["amount"],
                                                "priceUnit": "$",
                                                "oversold": oversold,
                                            }
                                            specs.append(spec)
                                    except:
                                        pass

        imgs = []
        for color_li in color_list:
            color_item = color_li["products"][0]
            images = json_data["jsonConfig"]["images"]
            for (image_key, image_value) in images.items():
                if image_key == color_item:
                    for image in image_value:
                        img = image['img']
                        imgs.append(img)

        pattern = r'"description":(.*?),"image"'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        description = []
        description_data = result.group(1)
        pattern = r'>(.*?)<'

        clean_text = re.findall(pattern, description_data.replace('\n', ''))
        if clean_text != [] and clean_text != ['']:
            for clean in clean_text:
                if clean.replace(' ', '').replace('\r', '') != '':
                    description.append(clean)
        else:
            description = [description_data.replace('\\n', '').replace('\\r', '').replace('"', '')]

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

    execute('scrapy crawl minnetonkamoccasin:goods_all_list'.split(' '))
