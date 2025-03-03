# -*- coding: utf-8 -*-
# @Time : 2024-04-19 11:55
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
    name = 'rogervivier:goods_all_list'
    platform = "rogervivier"
    task_id = 'rogervivier'
    sch_task = 'rogervivier-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
            'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        },
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

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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
        page = 1
        urls = [
            'https://www.rogervivier.com/us-en/Must-haves/Bridal-Collection/c/212/page/1/'
            'https://www.rogervivier.com/us-en/New-Arrivals/See-all/c/103/page/1/',
            'https://www.rogervivier.com/us-en/Must-haves/Spring-Summer-2024-Collection/c/146/page/1/',
            'https://www.rogervivier.com/us-en/Must-haves/The-Iconics/c/198/page/1/',
            "https://www.rogervivier.com/us-en/Must-haves/Viv'-Choc/c/279/page/1/",
            "https://www.rogervivier.com/us-en/Must-haves/Viv'-Canard/c/156/page/1/",
            'https://www.rogervivier.com/us-en/Must-haves/Belle-Vivier/c/155/page/1/',
            'https://www.rogervivier.com/us-en/Shoes/All-Shoes/c/267/page/1/',
            'https://www.rogervivier.com/us-en/Bags/All-Bags/c/268/page/1/',
            'https://www.rogervivier.com/us-en/Accessories/All-Accessories/c/269/page/1/'
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_home,
                meta={'page': page}
                # headers=self.headers,
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """
        page = response.meta['page']
        div_list = response.xpath('//*[@id="categoryPage"]/div[12]/div[1]/div')
        if len(div_list) == 0:
            div_list = response.xpath('//*[@id="categoryPage"]/div[11]/div[1]/div')
        for div in div_list:
            try:
                url = div.xpath('./a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        # if len(div_list):
        #     page += 1
        #     url = response.url.split('page')[0] + 'page/%d/' % page
        #     yield scrapy.Request(
        #         url=url,
        #         callback=self.parse_home,
        #         meta={'page': page}
        #     )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["props"]["initialState"]["product"]["data"]["code"]
        skuid = json_data["props"]["initialState"]["product"]["data"]["code"]
        title = json_data["props"]["initialState"]["product"]["data"]["name"]
        cur_price = json_data["props"]["initialState"]["product"]["data"]["price"]["salePriceValue"]
        # cur_price = float(str(cur_price)[:-2] + '.' + str(cur_price)[-2:])
        ori_price = json_data["props"]["initialState"]["product"]["data"]["price"]["fullPriceValue"]
        # ori_price = float(str(ori_price)[:-2] + '.' + str(ori_price)[-2:])
        color = json_data["props"]["initialState"]["product"]["data"]["color"]["current"]
        oversold_all = not json_data["props"]["initialState"]["product"]["data"]["isStockAvailable"]
        brand = 'Roger Vivier'

        pattern = r'firstLevelCategory":"(.*?)",'
        result = re.search(pattern, data_start)
        firstLevelCategory = result.group(1)

        pattern = r'secondLevelCategory":"(.*?)",'
        result = re.search(pattern, data_start)
        secondLevelCategory = result.group(1)

        pattern = r'thirdLevelCategory":"(.*?)",'
        result = re.search(pattern, data_start)
        thirdLevelCategory = result.group(1)

        breadlist = f'{firstLevelCategory} / {secondLevelCategory} / {thirdLevelCategory}'

        try:
            summary = json_data["props"]["initialState"]["product"]["data"]["summary"]
            description = [summary]
            description_data = json_data["props"]["initialState"]["product"]["data"]["description"][0]
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
        except:
            description = []

        variants = json_data["props"]["initialState"]["product"]["data"]["size"]["variants"]

        specs = []
        for variant in variants:
            stockLevelStatus = variant["stockLevelStatus"]
            if stockLevelStatus == 'OUTOFSTOCK':
                oversold = True
            else:
                oversold = False
            spec = {
                'spec': f'{color} / {variant["sizeCode"]}',
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": oversold
            }
            specs.append(spec)

        imgs = []
        imgs_list = response.xpath('//*[@id="productPageContainer"]/div[7]/section/div[1]/div[1]/div/div')
        for img in imgs_list:
            try:
                url = 'https:' + img.xpath('./div/picture/source[1]/@srcset').extract()[0]
                imgs.append(url)
            except:
                pass

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

    execute('scrapy crawl rogervivier:goods_all_list'.split(' '))
