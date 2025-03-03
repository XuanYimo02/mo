# -*- coding: utf-8 -*-
# @Time : 2024-03-21 14:04
# @Author : Mo

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import warnings
import traceback
from datetime import datetime
from urllib.parse import urljoin, urlencode
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
    name = 'balmain:goods_all_list'
    platform = "balmain"
    task_id = 'balmain'
    sch_task = 'balmain-task'
    today = datetime.now()
    log_file_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_logs//{platform}_{today.year}_{today.month}_{today.day}.log'
    auto_parse_info_path = f'{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}//spider_parse_infos//{platform}.json'
    custom_settings = {
        "ITEM_PIPELINES": {
            'dmscrapy.pipelines.DmDataDisPipeline2': 100,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # "oversea_mall.middlewares.OverseaProxyMiddleware": 200,
        },
        # 'DOWNLOAD_HANDLERS': {
        #     'http': 'oversea_mall.middlewares.RequestsDownloadHandler',
        #     'https': 'oversea_mall.middlewares.RequestsDownloadHandler',
        # },
        "EXTENSIONS": {
            'dmscrapy.extensions.DmSpiderSmartIdleClosedExensions': 500
        },
        "CONTINUOUS_IDLE_NUMBER": 12,
        'CONCURRENT_REQUESTS': 5,
        "DOWNLOAD_DELAY": 0,
        'DOWNLOAD_TIMEOUT': 10,
        "LOG_LEVEL": "INFO",
        "EXIT_ENABLED": True,
        'LOG_FILE': log_file_path,
        'LOG_STDOUT': True,
        # 'REDIRECT_ENABLED': False
    }

    headers = {
        "authority": "us.balmain.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "$cookie": "selectedCountry=US; selectedLocale=en_US; __cq_uuid=acwYEcClSW7azJ9i4xUWgCOByO; dwanonymous_92cf0c147968b91a7a7c01b73ddf7df5=bdwzbTfiURLmAq4YfSoaVVgLmu; selectedCountry=US; selectedLocale=en_US; lastViewedProducts=CF0R2320LD13GAB|3615884690994|CN0XH307KCXI1CA|CN0XH307KCXI0DP; __cq_bc=%7B%22bhgx-balmain-us%22%3A%5B%7B%22id%22%3A%22CN0XH307KCXI%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22CN0XH307KCXI0DP%22%7D%2C%7B%22id%22%3A%22CN0XH307KCXI%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22CN0XH307KCXI1CA%22%7D%2C%7B%22id%22%3A%22CN0DB903KTGL%22%2C%22sku%22%3A%223615884690994%22%7D%2C%7B%22id%22%3A%22AN1AE742LPRS%22%2C%22sku%22%3A%223615884181522%22%7D%2C%7B%22id%22%3A%22CF2R2220VF10%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22CF2R2220VF10AAA%22%7D%2C%7B%22id%22%3A%22CF0RJ013KG31%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22CF0RJ013KG31GQV%22%7D%5D%7D; dwac_283320b09f97a5e8c244049b40=kbdTHra6589YUSDg5q7fKx7qTQk7FNmIIK8%3D|dw-only|||USD|false|US%2FCentral|true; cqcid=bdwzbTfiURLmAq4YfSoaVVgLmu; cquid=||; sid=kbdTHra6589YUSDg5q7fKx7qTQk7FNmIIK8; __cq_dnt=0; dw_dnt=0; dwsid=vGtwKL8TpDptQgi-6ygQzzM2bj8yvZp9FbxrqSfHhHFmb9grzL_tWGqGdbMUlWUoH_9ae9NUMGFu4h-tVsqIYQ==; _gcl_au=1.1.601032834.1711072867; _ga=GA1.1.1354642320.1711072867; _gid=GA1.2.994995063.1711072867; _sp_ses.8072=*; _cs_c=0; _clck=15ktfqq%7C2%7Cfka%7C0%7C1542; mp_cbed09644a7d342ee435878a7bfc2238_mixpanel=%7B%22distinct_id%22%3A%20%22%24device%3A18e5f959914ea4-0d56c49024cba5-4c657b58-1fa400-18e5f959914ea4%22%2C%22%24device_id%22%3A%20%2218e5f959914ea4-0d56c49024cba5-4c657b58-1fa400-18e5f959914ea4%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fus.balmain.com%2Fen%2Fwomen%2Fready-to-wear%2F%22%2C%22%24initial_referring_domain%22%3A%20%22us.balmain.com%22%2C%22__mps%22%3A%20%7B%22%24os%22%3A%20%22Windows%22%2C%22%24browser%22%3A%20%22Microsoft%20Edge%22%2C%22%24browser_version%22%3A%20122%2C%22body-settings__color%22%3A%200%2C%22body-settings__braCupSize%22%3A%20%22B%22%2C%22body-settings__breastsHeight%22%3A%2050%2C%22body-settings__breastsDistance%22%3A%2050%2C%22body-settings__buttocksFullness%22%3A%2050%2C%22body-settings__buttocksSquareRound%22%3A%2050%2C%22body-settings__buttocksHeartInverted%22%3A%2050%2C%22body-settings__curves%22%3A%2050%2C%22body-settings__arms%22%3A%2050%2C%22body-settings__waist%22%3A%2050%2C%22body-settings__thighs%22%3A%2050%2C%22body-settings__Abdomen%22%3A%2050%2C%22b__is-registered%22%3A%20false%7D%2C%22__mpso%22%3A%20%7B%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fus.balmain.com%2Fen%2Fwomen%2Fready-to-wear%2F%22%2C%22%24initial_referring_domain%22%3A%20%22us.balmain.com%22%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22body-settings__color%22%3A%200%2C%22body-settings__braCupSize%22%3A%20%22B%22%2C%22body-settings__breastsHeight%22%3A%2050%2C%22body-settings__breastsDistance%22%3A%2050%2C%22body-settings__buttocksFullness%22%3A%2050%2C%22body-settings__buttocksSquareRound%22%3A%2050%2C%22body-settings__buttocksHeartInverted%22%3A%2050%2C%22body-settings__curves%22%3A%2050%2C%22body-settings__arms%22%3A%2050%2C%22body-settings__waist%22%3A%2050%2C%22body-settings__thighs%22%3A%2050%2C%22body-settings__Abdomen%22%3A%2050%2C%22b__is-registered%22%3A%20false%7D; cto_bundle=Sxe-il9PU1pXQlBIUHZRRU5tRms4dUh5bVptMjY1dmpNTFhMbVFuT0tkVyUyQmNmJTJGU2RuSm5UbnRjdlZkczBhNzNDOHUza3k0WGpnWjBNMkJPcDdvVTZNZFBwVExuVjZEJTJGQU1kdzZvMFF3Z3JpOVNnREglMkIxbEQzbGQ0UXdZaTg3OEI1YVBGNHphOWJtdSUyQnEyWEVnN1QyNXVPYjV3JTNEJTNE; _clsk=15aouaz%7C1711073162854%7C2%7C1%7Cl.clarity.ms%2Fcollect; _ga_3PVHTKHPQ4=GS1.1.1711072866.1.1.1711073505.0.0.0; _uetsid=104a9270e7f011eebc152bcb72215269; _uetvid=104ab640e7f011eebee94382cdc6d9f1; _cs_id=66e42314-bc47-aab6-aa3b-67f8f453aa7e.1711072867.1.1711073505.1711072867.1.1745236867420.1; _cs_s=3.0.0.1711075305653; __cq_seg=0~-0.14\\u00211~0.02\\u00212~0.17\\u00213~0.49\\u00214~-0.11\\u00215~-0.31\\u00216~-0.52\\u00217~-0.03\\u00218~-0.33\\u00219~-0.47\\u0021f0~15~5\\u0021n0~1; _sp_id.8072=c70a15d2-dfc9-421d-a5da-16964751bb3e.1711000080.4.1711073507.1711011632.d812307f-85f0-47c8-88e8-6842ef8061b8",
        "referer": "https://us.balmain.com/en/women/accessories/",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
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
            'https://us.balmain.com/en/men-1/',
            'https://us.balmain.com/en/women-2',
            'https://us.balmain.com/en/kids/'
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                dont_filter=False,
                callback=self.parse_home,
                headers=self.headers
            )

    async def parse_home(self, response, **kwargs):
        """
        爬虫首页抓取
        """

        pages = int(response.xpath('//*[@class="header page-title"]/@data-count-product').extract()[0])
        global cqid
        if 'men' in response.url:
            cqid = 'men'

        if 'women' in response.url:
            cqid = 'women'

        if 'kids' in response.url:
            cqid = 'kids'
        for page in range(0, (pages - 1) // 16 + 1):
            if page == (pages - 1) // 16:
                sz = pages - page * 16
            else:
                sz = 16
            params = {
                "cgid": f"{cqid}",
                "start": f"{16 * page}",
                "sz": f"{sz}",
            }

            url = "https://us.balmain.com/en/search/grid?" + urlencode(params)

            yield scrapy.Request(
                url=url,
                dont_filter=False,
                callback=self.parse_list,
                headers=self.headers
            )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        div_list = response.xpath('//*[@class="tile-box"]')
        for div in div_list:
            pid = div.xpath('./a/@href').extract()[0]
            detail_url = "https://us.balmain.com/" + pid
            yield scrapy.Request(
                url=detail_url,
                dont_filter=False,
                callback=self.parse_detail,
                headers=self.headers,
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫款式抓取
        """
        pid = response.url.split('-')[-1].split('.')[0]

        params = {
            "filteredValues": "true",
            "pid": f"{pid}"
        }
        detail_url = 'https://us.balmain.com/en/product/variation?'+urlencode(params)
        yield scrapy.Request(
            url=detail_url,
            dont_filter=False,
            callback=self.parse_de_detail,
            headers=self.headers,
        )

    async def parse_de_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        global oversold_all, color
        json_data = response.json()
        product = json_data['product']
        itemid = product["analytics"]["item_master"]
        skuid = product['id']
        title = product['productName']
        cur_price = float(product['price']['sales']['decimalPrice'])
        ori_price = float(product['price']['sales']['decimalPrice'])
        larges = product["images"]["large"]
        breadlist = product["categoryPath"].replace('>', '/')
        brand = self.platform
        productUrl = product['productUrl']
        imgs = []
        for large in larges:
            img = large['absURL']
            imgs.append(img)

        values = product['variationAttributes'][1]['values']
        vals = product['variationAttributes'][0]['values']

        for val in vals:
            if val['selected'] == True:
                oversold_all = not val['selectable']
                color = val["value"]

        specs = []
        for value in values:
            oversold = not value['selectable']
            size = value['id']

            spec = {
                "spec": f'{color} / {size}',
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": oversold,
            }
            specs.append(spec)

        description = []
        shortDescription = product['shortDescription']
        pattern = r'>(.*?)<'

        clean_text = re.findall(pattern, shortDescription.replace('\n', ''))
        for clean in clean_text:
            if clean.replace(' ', '') != '':
                description.append(clean)

        oss_imgs = imgs
        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": itemid,
            "skuid": skuid,
            "title": title,
            "price": cur_price,
            "orig_price": ori_price,  # 没有原价，只有一个价格怎么存，存price还是ori_price
            "price_unit": "$",
            "prices": {"US": {"p": cur_price, "o": ori_price, 'u': "$"}},
            "specs": specs,
            "imgs": oss_imgs,
            "pic_url": oss_imgs[0],
            "orig_imgs": imgs,
            "orig_main_pic": imgs[0],
            "detail_url": productUrl,  # 网页还是信息页
            "brand_name": brand,
            "category_info": breadlist,
            "description": description,
            "insert_time": get_now_datetime(),
            "online": True,
            "oversold": oversold_all
        }
        logger.info(item)

        data = PostData()
        data['dataRows'] = [item]
        data['name'] = 'goods_base'
        data[defaults.DM_SCHEDULER_TASK_ID] = response.meta.get(defaults.DM_SCHEDULER_TASK_ID)
        data[defaults.DM_SCHEDULER_FORCE_TASK] = response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)

        yield data


if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl balmain:goods_all_list'.split(' '))
