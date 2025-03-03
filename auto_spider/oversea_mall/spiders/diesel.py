# -*- coding: utf-8 -*-
# @Time : 2024-05-22 14:26
# @Author : Mo

import logging
import os
import sys

import curl_cffi.requests
from scrapy import Selector

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
    name = 'diesel:goods_all_list'
    platform = "diesel"
    task_id = 'diesel'
    sch_task = 'diesel-task'
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

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryyO4eAO72eTG1wa1o",
        "$cookie": "utagdb=false; dwanonymous_06fd9c6d4fc17274b498b31014b05f19=abUXtj175yEbNgm63YzIjJMzkV; adms_channel=Typed/Bookmarked; DIESELCONSENTV2=c1:1%7Cc3:1%7Cc7:1%7Cc9:1%7Cc14:1%7Cts:1715653169419%7Cconsent:true; __cq_uuid=abQ8PXM68VHRO5Xl6U6OLstXT4; _gcl_au=1.1.1103297026.1715653175; _ga=GA1.1.1457602146.1715653175; _scid=551be75d-7b2e-4fdf-9aba-2b5755640a0c; _cs_c=0; _tt_enable_cookie=1; _ttp=ChtN30v82ZZABitn8kikYNeoZbF; MADid=f444e9db-7dea-490f-9379-cf03101e0d4c; dwmaduuid=ceaaa4b8-21f6-404f-b565-e73ec27278f5; rskxRunCookie=0; rCookie=giwkim0gtpr31m8wc7nsr3lw5rm0fz; mdLogger=false; kampyle_userid=dd5d-3aab-0c19-756d-6959-c323-0319-4d6f; _aeaid=1ccd7b93-c5bf-4df6-b545-21a8461089a5; aelastsite=okLVS45%2Fkk3F9Tg5pdD%2FIsDhn7XGUQq9dgGwWvZzdI6LcySnlS%2B8PF1kPxcg3KEo; dwsid=I_AbcD9jISwkgSaKPz9HTqtbxCqOAKtKqDQrPPnyaGax0TqoGdFEUR8UUThodQdzwYWeSduHay3xvTN7zRZJLQ==; dwac_9adf6f0def957648953250840e=qBA2gljrp1bbBkonVNkf7yC76djpiC0wV7M%3D|dw-only|||USD|false|US%2FEastern|true; cqcid=abUXtj175yEbNgm63YzIjJMzkV; cquid=||; sid=qBA2gljrp1bbBkonVNkf7yC76djpiC0wV7M; GlobalE_Data=%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22en-US%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D; __cq_dnt=0; dw_dnt=0; check=true; AMCVS_982E985B591252110A495C70%40AdobeOrg=1; gvsC=New; fb_test=B; s_cc=true; GlobalE_Full_Redirect=false; _sctr=1%7C1716307200000; aelreadersettings=%7B%22c_big%22%3A0%2C%22rg%22%3A0%2C%22memph%22%3A0%2C%22contrast_setting%22%3A0%2C%22colorshift_setting%22%3A0%2C%22text_size_setting%22%3A0%2C%22space_setting%22%3A0%2C%22font_setting%22%3A0%2C%22k%22%3A0%2C%22k_disable_default%22%3A0%2C%22hlt%22%3A0%2C%22disable_animations%22%3A0%2C%22display_alt_desc%22%3A0%7D; s_ppv=100; mboxEdgeCluster=35; s_dfa=diesel.prod; aa_dslv_s=Less%20than%201%20day; AMCV_982E985B591252110A495C70%40AdobeOrg=1278862251%7CMCIDTS%7C19866%7CMCMID%7C85315959859533080903086445444766289329%7CMCAAMLH-1716974587%7C9%7CMCAAMB-1716974587%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1716376987s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.0.0; kampyleUserSession=1716371071783; kampyleUserSessionsCount=14; dwproduct=\"8058992759187,A13972068MI01,A124030DLAX9XX\"; __cq_bc=%7B%22bblg-DieselUS%22%3A%5B%7B%22id%22%3A%22X08396P6248%22%2C%22sku%22%3A%228058992759187%22%7D%2C%7B%22id%22%3A%22A124030DLAX%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22A124030DLAX9XX%22%7D%2C%7B%22id%22%3A%22Y03210PR271%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22Y03210PR271T8013%22%7D%2C%7B%22id%22%3A%22PL038900PRO%22%2C%22sku%22%3A%228059966624999%22%7D%2C%7B%22id%22%3A%22A13972068MI%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22A13972068MI01%22%7D%2C%7B%22id%22%3A%22Y03073P0423%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22Y03073P0423T8013%22%7D%2C%7B%22id%22%3A%22Y03073P0423%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22Y03073P0423T1003%22%7D%5D%7D; prod_find_method=listing; __cq_seg=0~0.35\\u00211~-0.42\\u00212~0.01\\u00213~-0.01\\u00214~0.36\\u00215~0.03\\u00216~0.63\\u00217~0.06\\u00218~0.39\\u00219~-0.13\\u0021f0~15~5; _cs_mk=0.4583499874677348_1716371766970; aa_prev_page=us%3Aman%3Adenimandclothing%3Adenim; _uetsid=74269810180211efaaa5795faefdcb15; _uetvid=69ee1f20119811ef8d4a3bc5a27ada6d; _ga_7LBLR8C5RF=GS1.1.1716369779.3.1.1716371768.0.0.0; _ga_YT7XV1WTS6=GS1.1.1716369779.3.1.1716371768.0.0.0; _scid_r=551be75d-7b2e-4fdf-9aba-2b5755640a0c; _cs_id=6ebcabe6-745a-a9f2-d8f8-3a9c74cf876f.1715653179.3.1716371769.1716369515.1.1749817179073.1; _cs_s=11.0.0.1716373569339; GlobalE_CT_Data=%7B%22CUID%22%3A%7B%22id%22%3A%22643071954.427007166.1389%22%2C%22expirationDate%22%3A%22Wed%2C%2022%20May%202024%2010%3A26%3A10%20GMT%22%7D%2C%22CHKCUID%22%3Anull%2C%22GA4SID%22%3A294232910%2C%22GA4TS%22%3A1716371770421%7D; inside-eu2=770970161-7bdc630551843bc0e773ed3a9e5d37d35eb255152820a15bbf3a81c867f580e0-0-0; kampyleSessionPageCounter=6; lastRskxRun=1716371771425; utag_main=v_id:018f74e5cc1e001e5591593265330506f001b06700bd0$_sn:3$_ss:0$_st:1716373572250$vapi_domain:diesel.com$ses_id:1716369780799%3Bexp-session$_pn:7%3Bexp-session; aa_dslv=1716371772254; aa_newrep=1716371772255-Repeat; aeatstartmessage=true; mbox=PC#8c4e9b4c230b40cbafd5fb037b9e6e9c.35_0#1779616597|session#af66ceff51b14a05908036769b26121f#1716373657; RT=\"z=1&dm=diesel.com&si=89282bcd-cbd1-4256-b8eb-4c32a6150dab&ss=lwhmshhq&sl=2&tt=ixx&bcn=%2F%2F17de4c0d.akstat.io%2F&ld=n8j0&nu=1axx93y7i&cl=nt5z\"; aa_cvpmc_n=%5B%5B%27Typed%2FBookmarked%27%2C%271716371808699%27%5D%5D; s_sq=diesel.prod%3D%2526pid%253Dus%25253Aman%25253Adenimandclothing%25253Adenim%2526pidt%253D1%2526oid%253D%25250A%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520Load%252520more%25250A%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%252520%2526oidt%253D3%2526ot%253DSUBMIT",
        "origin": "https://shop.diesel.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://shop.diesel.com/en/mens/denim/?cgid=diesel-man-denimandclothing-denim&prefn1=displayOnlyOnSale&prefv1=false&start=60&sz=60&lastAction=grid",
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
                'https://shop.diesel.com/en/sale/mens/',
                'https://shop.diesel.com/en/mens/denim/',
                'https://shop.diesel.com/en/mens/apparel/',
                'https://shop.diesel.com/en/mens/bags/',
                'https://shop.diesel.com/en/mens/footwear/',
                'https://shop.diesel.com/en/mens/accessories/',
                'https://shop.diesel.com/en/mens/fragrances/',
                'https://shop.diesel.com/en/mens/watches-and-jewelry/',
                'https://shop.diesel.com/en/womens/denim/',
                'https://shop.diesel.com/en/womens/apparel/',
                'https://shop.diesel.com/en/womens/bags/',
                'https://shop.diesel.com/en/womens/footwear/',
                'https://shop.diesel.com/en/womens/accessories/',
                'https://shop.diesel.com/en/watches-and-smartwatches/',
                'https://shop.diesel.com/en/womens/fragrances/',
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
        cgid = response.xpath('//*[@id="main-header"]/@data-querystring').extract()[0].split('cgid=')[-1]
        params = {
            "cgid": cgid,
            "start": "0",
            "sz": "60"
        }
        url = response.url + '?' + urlencode(params)

        yield scrapy.Request(
            url=url,
            callback=self.parse_list,
            headers=self.headers,
            meta={'page': 0, 'cgid': cgid, 'ori_url': response.url}
        )

    async def parse_list(self, response, **kwargs):
        """
        爬虫列表页抓取
        """
        meta = response.meta
        page = meta['page']
        cgid = meta['cgid']
        ori_url = meta['ori_url']
        div_list = response.xpath('/html/body/div[4]/div')
        if len(div_list) == 1:
            div_list = response.xpath('/html/body/div[3]/div')
        for div in div_list:
            try:
                url = div.xpath('./div/div/div[2]/div[2]/div[1]/a/@href').extract()[0]
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                )
            except:
                pass

        # print(len(div_list), response, page)
        if len(div_list):
            page += 1
            meta['page'] = page
            meta['cgid'] = cgid
            meta['ori_url'] = ori_url
            params = {
                "cgid": cgid,
                "start": str(60*page),
                "sz": "60"
            }
            url = ori_url + '?' + urlencode(params)

            yield scrapy.Request(
                url=url,
                callback=self.parse_list,
                headers=self.headers,
                meta=meta,
            )

    @AutoParse.check_parse_info
    async def parse_detail(self, response, **kwargs):
        """
        爬虫详情页抓取
        """
        allProductIds = response.xpath('//*[@id="product-content__body"]/div[4]/div/div/a')

        for ProductId in allProductIds:
            url = ProductId.xpath('./@href').extract()[0]
            yield scrapy.Request(
                url=url,
                callback=self.parse_item_detail,
                headers=self.headers,
                dont_filter=True
            )

    async def parse_item_detail(self, response, **kwargs):
        pattern = r'window.utag_data = (.*?);</script>'
        data_start = response.text.replace('\n', '')
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))

        itemid = json_data["product_id"][0]
        skuid = json_data["product_sku"][0]
        title = json_data["page_name"]
        brand = json_data["product_brand"]
        breadlist = json_data["product_category"]
        cur_price = float(json_data["product_sale_price"][0])
        ori_price = json_data["product_old_price"][0]
        if ori_price == '':
            ori_price = cur_price
        else:
            ori_price = float(ori_price)

        description = []
        descriptions_list = response.xpath('//*[@class="value content value-regular"]/text()').extract()
        for des in descriptions_list:
            description.append(des.replace('\n', '').replace(' ', ''))

        imgs = []
        pattern = r'<script type="application/ld\+json">(.*?}})'
        result = re.search(pattern, data_start)
        image_data = json.loads(result.group(1))
        images = image_data["image"]
        for image in images:
            imgs.append(image)

        pattern = r'  window.fitAnalyticsData = (.*?});</script>'
        result = re.search(pattern, data_start)
        json_data = json.loads(result.group(1))
        oversold_all = True
        specs = []
        variants = json_data["sizes"]
        for variant in variants:
            if variant["value"]:
                oversold_all = False
            spec = {
                'spec': variant["value"],
                "price": cur_price,
                "origPrice": ori_price,
                "priceUnit": "$",
                "oversold": not variant["value"]
            }
            specs.append(spec)

        oss_imgs = get_oss_imgs(self.platform, imgs)
        await download_imgs(self.platform, imgs, skuid)
        item = {
            "platform": self.platform,
            "itemid": str(itemid),
            "skuid": str(skuid),
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

    execute('scrapy crawl diesel:goods_all_list'.split(' '))
