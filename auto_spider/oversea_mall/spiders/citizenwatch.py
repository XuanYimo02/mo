# -*- coding: utf-8 -*-
# @Time : 2024-05-28 16:37
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
    name = 'citizenwatch:goods_all_list'
    platform = "citizenwatch"
    task_id = 'citizenwatch'
    sch_task = 'citizenwatch-task'
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
            'https://www.citizenwatch.com/us/en/collection/mens/',
            'https://www.citizenwatch.com/us/en/collection/womens/',
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
        cgid = response.url.split('/')[-2]
        params = {
            "cgid": cgid,
            "start": "0",
            "sz": "48",
            "selectedUrl": "https://www.citizenwatch.com/on/demandware.store/Sites-citizen_US-Site/en_US/Search-UpdateGrid?cgid=mens&start=0&sz=48"
        }
        url = "https://www.citizenwatch.com/on/demandware.store/Sites-citizen_US-Site/en_US/Search-UpdateGrid?" + urlencode(params)
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
        cgid = meta['cgid']
        page = meta['page']
        div_list = response.xpath('/html/body/div')
        for div in div_list:
            try:
                url = 'https://www.citizenwatch.com' + div.xpath('./div/div/div[2]/div[2]/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        # print(len(div_list),response)
        if len(div_list) > 1:
            page += 48
            meta['cgid'] = cgid
            meta['page'] = page
            params = {
                "cgid": cgid,
                "start": page,
                "sz": "48",
                "selectedUrl": f"https://www.citizenwatch.com/on/demandware.store/Sites-citizen_US-Site/en_US/Search-UpdateGrid?cgid={cgid}&start={page}&sz=48"
            }
            url = "https://www.citizenwatch.com/on/demandware.store/Sites-citizen_US-Site/en_US/Search-UpdateGrid?" + urlencode(params)
            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                meta=meta
            )


    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        itemid = response.url.split('.html')[0].split('/')[-1]
        skuid = response.url.split('.html')[0].split('/')[-1]
        cur_price = float(response.xpath('//*[@class="sales"]/span/@content').extract()[0])
        try:
            ori_price = float(response.xpath('//*[@class="show-more-text-content"]/span/@content').extract()[0])
        except:
            ori_price = cur_price
        description = [response.xpath('//*[@id="collapse-long-description"]/p/text()').extract()[0].replace('\n', '').strip()]
        oversold_all = False

        try:
            pattern = r',"category":"(.*?)",'
            data_start = response.text.replace('\n', '')
            result = re.search(pattern, data_start)
            breadlist = result.group(1)
        except:
            breadlist = response.xpath('//*[@id="maincontent"]/header/div/div/ol/li[2]/a/text()').extract()[0].replace('\n', '').replace(' ', '').split("'s")[0]

        specs = []
        specs_list = response.xpath('//*[@class="options-select custom-select form-control"]/option//text()').extract()
        for spe in specs_list[:len(specs_list)//2]:
            if not('Band Size' in spe or 'No Size Adjustments' in spe):
                spec = {
                    'spec': spe.replace('\n', '').strip(),
                    "price": cur_price,
                    "origPrice": ori_price,
                    "priceUnit": "$",
                    "oversold": False
                }
                specs.append(spec)

        pattern = r'<script type="application/ld\+json">(.*?)    </script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        brand = json_data["brand"]["name"]
        title = json_data["name"]

        imgs = []
        images = json_data["image"]
        for image in images:
            imgs.append(image)

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

    execute('scrapy crawl citizenwatch:goods_all_list'.split(' '))
