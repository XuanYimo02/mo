# -*- coding: utf-8 -*-
# @Time : 2024-06-18 17:38
# @Author : Mo

import copy
import logging
import os
import sys
import urllib

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
    name = 'louxly:goods_all_list'
    platform = "louxly"
    task_id = 'louxly'
    sch_task = 'louxly-task'
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
    base_url = "https://louxly.com"
    UUID = ""
    filter_url = "" # 自己加    # 根据网站的值自己加
    filter_params_shop = "" # 自己加 # 根据网站的值自己加
    queries_url = ""     # 根据网站的值自己加
    queries_params = {
        "x-algolia-agent": "Algolia for JavaScript (4.5.1); Browser (lite)",
        "x-algolia-api-key": "",     # 根据网站的值自己加
        "x-algolia-application-id": ""   # 根据网站的值自己加
    }
    queries_data_indexName = "" # 根据网站的值自己加

    domain = base_url.split("/")[2]
    new_base_url = f"https://{domain}"
    whileIf_dict = {}  # 跳出死循环条件 不需要更改
    web_suffix = "." + base_url.split(".")[-1].split("/")[0]  # 这个网站的后缀
    price_unit = "$"  # 货币类型 有些没有美元
    page = "page"  # 这个有可能会变 遇到一个用pg的
    debugger = 0
    whileIF_text = debugger  # 1开启page调试 有些太多 会不出结果  0关闭 上传服务器关闭
    debug_IF = debugger  # 1开启调试 0关闭调试
    href_values_set = [

    ]  # 自己添加没识别到的列表url  没出值设置

    webPixelsManagerAPI_params = {
        page: str(1),
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "referer": base_url,
        "sec-ch-ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    cookies = {
        "localization": "US",  # 货币类型基本都是这个指定
        "cart_currency": "USD",  # 货币类型基本都是这个指定
    }
    proxies = {}
    xpath_list = {}
    json_list = {}
    def start_requests(self):
        url = self.base_url
        yield scrapy.Request(
            url=url,
            callback=self.get_home_urls,
            headers=self.headers,
            cookies=self.cookies
        )

    def get_home_urls(self, response, **kwargs):
        # print("get_home_urls")
        import urllib
        href_regex = r'<a\s+[^>]*href="([^"]*)"'
        href_values = re.findall(href_regex, response.text)
        # 输出提取到的href值
        unique_urls = set()
        for i in self.href_values_set:
            href_values.append(i)
        print("href_values: " + str(len(href_values)))
        print(href_values)
        for href in href_values:
            if "collections" in href and "products" not in href and "?" not in href:
                if self.queries_url != "":
                    print("进入queries规则" + " --- " + href)

                    data = {
                        "requests": [
                            {
                                "indexName": self.queries_data_indexName,
                                "params": "filters=collections%3A%22" + href.split("collections/")[-1] + "%22&"
                                                                                                         "hitsPerPage=60&"
                                                                                                         "page=3&"
                            }
                        ]
                    }
                    meta = {
                        "data": data
                    }
                    full_url = self.queries_url + '?' + urllib.parse.urlencode(self.queries_params)
                    yield scrapy.Request(
                        method='POST',  # 指定请求方法为POST
                        url=full_url,
                        callback=self.get_queries_pages,
                        body=json.dumps(data),  # 将POST数据转换成JSON格式的字符串
                        headers=self.headers,
                        cookies=self.cookies,
                        meta=meta,
                        dont_filter=True
                    )
                elif self.filter_url != "":
                    print("进入filter规则" + " --- " + href)
                    url = self.new_base_url + href
                    count_https = url.count("https://")
                    if count_https > 1:
                        continue
                    webPixelsManagerAPI_params = self.webPixelsManagerAPI_params.copy()
                    # for i in range(1,5):
                    page_value = 1
                    webPixelsManagerAPI_params[self.page] = str(page_value)
                    full_url = url + '?' + urllib.parse.urlencode(webPixelsManagerAPI_params)
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.get_filter_collection_scope,
                        headers=self.headers,
                        cookies=self.cookies,
                    )
                elif self.UUID != "":
                    print("进入categories_navigation规则 UUID= " + self.UUID + " --- " + href)
                    url = "https://api.fastsimon.com/categories_navigation"
                    params = {
                        "UUID": self.UUID,
                        "page_num": "1",  # 页码
                        "facets_required": "1",
                        "related_search": "1",
                        "with_product_attributes": "1",
                        "products_per_page": "48",
                        "category_url": href  # 类别
                    }
                    meta = {
                        "params": params,
                        "url": url
                    }
                    full_url = url + '?' + urllib.parse.urlencode(params)
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.get_categories_navigation_pages,
                        headers=self.headers,
                        cookies=self.cookies,
                        meta=meta,
                        dont_filter=True,
                    )
                else:
                    print("进入webPixelsManagerAPI规则" + " --- " + href)
                    url = self.new_base_url + href
                    count_https = url.count("https://")
                    if count_https > 1:
                        continue
                    unique_urls.add(url)
                    self.whileIf_dict[url] = {
                        "list": [],
                        "data": "",
                        "paeIf": 1
                    }
                    page_value = 1
                    webPixelsManagerAPI_params = self.webPixelsManagerAPI_params.copy()
                    # for i in range(1,5):
                    webPixelsManagerAPI_params[self.page] = str(page_value)
                    full_url = url + '?' + urllib.parse.urlencode(webPixelsManagerAPI_params)
                    # print(full_url)
                    meta = {
                        "page": page_value
                    }
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.get_pages,
                        headers=self.headers,
                        cookies=self.cookies,
                        meta=meta,
                    )

    def get_queries_pages(self, response, **kwargs):
        meta = response.meta
        data = meta["data"]
        data_json = response.json()
        nbPages = data_json["results"][0]["nbPages"]
        for nbPage in range(nbPages):
            modified_data = copy.deepcopy(data)  # 复制一份数据，避免直接修改原始数据
            modified_data["requests"][0]["params"] = modified_data["requests"][0]["params"].replace("page=3",
                                                                                                    f"page={nbPage}")
            full_url = self.queries_url + '?' + urllib.parse.urlencode(self.queries_params)
            print(modified_data)
            yield scrapy.Request(
                method='POST',  # 指定请求方法为POST
                url=full_url,
                callback=self.get_queries_list,
                body=json.dumps(modified_data),  # 将POST数据转换成JSON格式的字符串
                headers=self.headers,
                cookies=self.cookies,
                meta=meta,
            )

    def get_queries_list(self, response, **kwargs):
        print("get_queries_list")
        data_json = response.json()
        hits = data_json["results"][0]["hits"]
        for hit in hits:
            handle = hit["handle"]
            url = self.base_url + "/products/" + handle + ".js"
            print(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers,
                cookies=self.cookies,
            )

    def get_filter_collection_scope(self, response, **kwargs):
        import urllib
        re_text = response.text
        match = re_text.split('webPixelsManagerAPI.publish("collection_viewed", ')[-1].split(');}')[0]
        json_data = json.loads(match)
        collection_scope = json_data["collection"]["id"]
        params = {
            # "t": "1716171551113",
            "shop": self.filter_params_shop,
            "page": "1",
            "limit": "36",
            # "sort": "manual",
            # "display": "grid",
            "collection_scope": collection_scope,
            # "product_available": "true",
            # "variant_available": "true",
            # "build_filter_tree": "true",
            # "check_cache": "true",
            # "sort_first": "available",
            # "callback": "BCSfFilterCallback",
            # "event_type": "init"
        }
        meta = {
            "params": params
        }
        full_url = self.filter_url + '?' + urllib.parse.urlencode(params)
        yield scrapy.Request(
            url=full_url,
            callback=self.get_filter_collection_scope_pages,
            headers=self.headers,
            cookies=self.cookies,
            dont_filter=True,
            meta=meta,
        )

    def get_filter_collection_scope_pages(self, response, **kwargs):
        import urllib
        meta = response.meta
        params = meta["params"]
        data_json = response.json()
        total_product = data_json["total_product"]
        page = int(total_product / 36)
        if total_product % 36 > 0:
            page += 1
        for i in range(1, page + 1):
            params['page'] = str(i)
            full_url = self.filter_url + '?' + urllib.parse.urlencode(params)
            yield scrapy.Request(
                url=full_url,
                callback=self.get_filter_list,
                headers=self.headers,
                cookies=self.cookies,
                dont_filter=True,
                meta=meta,
            )

    def get_filter_list(self, response, **kwargs):
        data_json = response.json()
        products = data_json["products"]
        for product in products:
            handle = product["handle"]
            url = self.base_url + "/products/" + handle + ".js"
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers,
                cookies=self.cookies
            )

    def get_categories_navigation_pages(self, response, **kwargs):
        import urllib

        meta = response.meta
        params = meta["params"]
        url = meta["url"]
        data_json = response.json()
        total_p = data_json["total_p"]
        for i in range(1, total_p + 1):
            params["page_num"] = str(i)
            # print(params)
            full_url = url + '?' + urllib.parse.urlencode(params)
            # print(full_url)
            yield scrapy.Request(
                url=full_url,
                callback=self.get_categories_navigation_list,
                headers=self.headers,
                cookies=self.cookies,
            )

    def get_categories_navigation_list(self, response, **kwargs):
        data_json = response.json()
        items = data_json["items"]
        for item in items:
            u = item["u"]
            url = self.base_url + u + ".js"
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                headers=self.headers,
                cookies=self.cookies,
            )

    def get_pages(self, response, **kwargs):
        import urllib
        re_text = response.text
        meta = response.meta
        url = ""
        try:
            url = response.url.split("?")[0]
            match = re_text.split('webPixelsManagerAPI.publish("collection_viewed", ')[-1].split(');}')[0]
            json_data = json.loads(match)
            # print(json_data)
            productVariants = json_data["collection"]["productVariants"]
            if len(productVariants) <= 0:
                if self.whileIf_dict[url]["data"] == "":
                    self.whileIf_dict[url]["data"] = "空 return"
                print("空 return= " + response.url + " (ovo) " + str(self.whileIf_dict))
                return
            productVariant_id_1 = productVariants[0]["id"]

            if productVariant_id_1 in self.whileIf_dict[url]["list"]:

                if self.whileIf_dict[url]["data"] == "":
                    self.whileIf_dict[url]["data"] = "重复 return"
                print("重复 return= " + response.url + " (ovo) " + str(self.whileIf_dict))
                return
            self.whileIf_dict[url]["list"].append(productVariant_id_1)
            if self.whileIF_text:
                if meta["page"] > 5:
                    if self.whileIf_dict[url]["data"] == "":
                        self.whileIf_dict[url]["data"] = "value return"
                    print("value return= " + " (ovo) " + str(self.whileIf_dict))
                    return
            for productVariant in productVariants:
                product = productVariant["product"]
                parse_detail_url = response.url.split(self.web_suffix)[0] + self.web_suffix + product["url"] + ".js"
                print("parse_list= " + parse_detail_url)
                yield scrapy.Request(
                    url=parse_detail_url,
                    callback=self.parse_detail,
                    headers=self.headers,
                    cookies=self.cookies
                )
            print("get_pages_url= " + response.url)
            meta["page"] += 1
            webPixelsManagerAPI_params = self.webPixelsManagerAPI_params.copy()
            webPixelsManagerAPI_params[self.page] = str(meta["page"])
            full_url = url + '?' + urllib.parse.urlencode(webPixelsManagerAPI_params)
            yield scrapy.Request(
                url=full_url,
                callback=self.get_pages,
                headers=self.headers,
                cookies=self.cookies,
                meta=meta,
            )
        except Exception as e:
            print(response.url + " --------- " + str(e))
            self.whileIf_dict[url]["data"] = str(e)
            return

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        if response.url.endswith(".js"):
            pass
        else:
            print("url endswith not is js")
            """
            适应自动解析
            """
            yield scrapy.Request(
                url=response.url + ".js",
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_detail,
            )
        try:
            data_json = response.json()
            # 获取描述，使用get方法避免KeyError异常
            descriptionA = data_json.get("description", "")
            descriptionB = Selector(text=descriptionA)
            descriptionCS = descriptionB.xpath("//text()").extract()
            description = []
            for descriptionC in descriptionCS:
                descriptionC_A = descriptionC.replace("<br>", "")
                descriptionC_None = descriptionC_A.strip()
                if descriptionC_None == "":
                    continue
                description.append(descriptionC_None)
            category_info = data_json.get("type", "")
            if category_info == "":
                category_info = str(data_json.get("vendor", ""))
            # 获取图片列表，使用get方法避免KeyError异常，并添加"https:"前缀
            imgs = data_json.get("images", [])
            imgs = ["https:" + url for url in imgs]
            # 获取oss_imgs，get_oss_imgs函数需要传入platform和imgs参数
            oss_imgs = get_oss_imgs(self.platform, imgs)
            specs = []
            variants = data_json.get("variants", [])
            for variant in variants:
                price = float("{:.2f}".format(int(variant.get("price", 0)) / 100))
                compare_at_price = variant.get("compare_at_price")
                if compare_at_price is not None and compare_at_price != 0:
                    orig_price = float("{:.2f}".format(int(compare_at_price) / 100))
                else:
                    orig_price = price
                spec = {
                    "spec": variant.get("title", ""),
                    "price": price,
                    "origPrice": orig_price,
                    "priceUnit": self.price_unit,
                    "oversold": not bool(variant["available"])
                }
                specs.append(spec)
            price = float("{:.2f}".format(int(data_json.get("price", 0)) / 100))
            compare_at_price = data_json.get("compare_at_price")
            if compare_at_price is not None and compare_at_price != 0:
                orig_price = float("{:.2f}".format(int(compare_at_price) / 100))
            else:
                orig_price = price
            detail_url = response.url
            detail_url = detail_url.split(".js")[0]
            item = {
                "platform": self.platform,
                "itemid": str(data_json.get("id", "")),
                "skuid": str(data_json.get("id", "")),
                "title": str(data_json.get("title", "")),
                "price": price,
                "orig_price": orig_price,
                "price_unit": self.price_unit,
                "prices": {"US": {"p": price, "o": orig_price, 'u': self.price_unit}},
                "imgs": oss_imgs,
                "pic_url": oss_imgs[0] if oss_imgs else "",
                "orig_imgs": imgs,
                "orig_main_pic": imgs[0] if imgs else "",
                "detail_url": detail_url,
                # "detail_url": data_json.get("url", ""),
                "brand_name": str(data_json.get("vendor", "")),
                "category_info": category_info,
                "specs": specs,
                "insert_time": get_now_datetime(),
                "online": True,
                "oversold": not bool(data_json["available"]),
                "description": description,
            }
            if self.debug_IF == 1:
                print(item)
            if self.debug_IF == 0:
                await download_imgs(self.platform, item["orig_imgs"], item["skuid"])
                item_list = []
                item_list.append(item)
                if len(item_list) > 0:
                    data = PostData()
                    data['dataRows'] = item_list
                    data['name'] = 'goods_base'
                    data[defaults.DM_SCHEDULER_TASK_ID] = response.meta.get(defaults.DM_SCHEDULER_TASK_ID)
                    data[defaults.DM_SCHEDULER_FORCE_TASK] = response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)
                    logger.info(data)
                    yield data
        except Exception as e:
            self.logger.error(f'{response.url} {e} {traceback.format_exc()}')
    def close_spider(self, spider):
        # 在爬虫关闭时执行的操作
        self.logger.info(f"爬虫关闭了！ {self.whileIf_dict}")

if __name__ == '__main__':
    from scrapy.cmdline import execute

    execute('scrapy crawl louxly:goods_all_list'.split(' '))








