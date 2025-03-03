# 输入五个页面信息
import json
import logging
import os
import threading
import func_timeout
import price_parser
import requests
from lxml import etree
import time
from scrapy import Selector
from auto_parse.get_json import Get_json_class
from auto_parse.get_xpath import Get_xpath_class
from auto_parse.tools import filter_html_label, get_info_from_xpath, get_info_from_json, get_old_parse_info

logger = logging.getLogger(__name__)


class myThread(threading.Thread):

    def __init__(self, url, item_tests, headers, cookies, proxies):
        threading.Thread.__init__(self)
        self.url = url
        self.item_tests = item_tests
        self.headers = headers
        self.cookies = cookies
        self.proxies = proxies


    def run(self):
        #请求链接、从源代码中提取json信息、提取og:image图片（如果有的话并且是大图，不需要额外找img_xpath）
        for i in self.item_tests:
            if i.get('url') == self.url:
                source = get_source(self.url, self.headers, self.cookies, self.proxies)
                if i.get('img'):
                    try:
                        img_download = requests.get(i.get('img'), timeout=10, headers=self.headers, stream=True, cookies=self.cookies, proxies=self.proxies)
                    except:
                        img_download = ''
                    i['img_download'] = img_download
                i['source'] = source
                if source:
                    # source = filter_html_label(source)
                    # source = etree.HTML(source.encode('utf-8'))
                    source = etree.HTML(source)
                    i['dom_source'] = source
                break

def get_source(url,headers, cookies, proxies):
    session = requests.session()
    try:
        res = session.get(url, headers=headers, timeout=15, cookies=cookies, verify=False, proxies=proxies, allow_redirects=False)
        logger.info(url + ' ' + str(res.status_code))
        if res.status_code == 200:
            return res.text
        else:
            return ''
    except:
        logger.error(f'{url}请求失败')
        return ''
def deal_web_datas(web_datas, headers, cookies, proxies):
    #读取cova提取的字段信息
    for web_data in web_datas:
        web_data['title'] = filter_html_label(web_data.get('title')).strip()
        web_data['brand'] = filter_html_label(web_data.get('brand')).strip()
        web_data['breadlist'] = [filter_html_label(i).strip() for i in web_data['breadlist']]
        web_data['category'] = filter_html_label(web_data.get('category')).strip()
        web_data['itemid'] = filter_html_label(web_data.get('itemid')).strip()
        web_data['skuid'] = filter_html_label(web_data.get('skuid')).strip()
        web_data['cur_price'] = price_parser.parse_price(filter_html_label(web_data.get('cur_price')).strip()).amount
        web_data['ori_price'] = price_parser.parse_price(filter_html_label(web_data.get('ori_price')).strip()).amount
        if web_data['ori_price'] != None and web_data['cur_price'] != None:
            web_data['ori_price'] = str(web_data['ori_price'])
            web_data['cur_price'] = str(web_data['cur_price'])
            web_data['price'] = ''
        else:
            web_data['price'] = str(web_data['cur_price'])
            web_data['cur_price'] = ''
            web_data['ori_price'] = ''
    threads = []
    for i in range(0, 5):
        # 创建4个新线程
        thread = myThread(web_datas[i].get('url'), web_datas, headers, cookies, proxies)
        # 开启新线程
        thread.start()
        # 添加新线程到线程列表
        threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()
    return web_datas

def auto_get_xpath(web_datas, headers, cookies, proxies):
    object_xpath = Get_xpath_class()
    object_xpath.headers = headers
    object_xpath.cookies = cookies
    object_xpath.proxies = proxies
    start_time = time.time()
    check_items = web_datas
    for find_item in web_datas:
        object_xpath.check_items = []
        for check_item in check_items:
            if find_item['url'] != check_item.get('url'):
                object_xpath.check_items.append(check_item)
        base_url = find_item['url']
        source = find_item.get('dom_source')
        if source:
            # logger.info(find_item['url'])
            # for id in ['img']:
            #     if object_xpath.xpath_lists[id] == [] and find_item.get(id):
            #         print(f'寻找{id} xpath')
            #         object_xpath.get_xpath(source, find_item.get(id), id)
            for id in ['title', 'price', 'ori_price', 'cur_price', 'brand', 'img', 'breadlist', 'itemid', 'category', 'skuid']:
                if object_xpath.xpath_lists[id] == [] and find_item.get(id):
                    logger.info(f'寻找{id} xpath')
                    try:
                        object_xpath.get_xpath(source, find_item.get(id), id)
                    except func_timeout.exceptions.FunctionTimedOut:
                        logger.info(f'寻找{id} xpath超时')
            for id in ['img_download']:
                # 得到img，图片相似度比较
                if object_xpath.xpath_lists['img'] == [] and find_item.get(id):
                    base_img_url = find_item.get('img')
                    logger.info(f'寻找{id} xpath')
                    try:
                        object_xpath.get_xpath_img(source, find_item.get(id), id, base_url, base_img_url)
                    except func_timeout.exceptions.FunctionTimedOut:
                        logger.info(f'寻找{id} xpath超时')

    result_xpath_lists = {
        'title': [],
        'price': [],
        'ori_price': [],
        'cur_price': [],
        'img': [],
        'brand': [],
        'breadlist': [],
        'itemid': [],
        'skuid': [],
        'category': []
    }

    for key, value in object_xpath.xpath_lists.items():
        for xpath in value:
            type = xpath.get('xpath_type')
            node_index = xpath.get('node_index')
            xpath = xpath.get('xpath')
            if key == 'title':
                if type == 1 and any(field in xpath for field in ['img', 'bread', '/li']) == False:
                    result_xpath_lists[key].append({'xpath':xpath,'node_index':node_index})
            else:
                if type == 1:
                    result_xpath_lists[key].append({'xpath':xpath,'node_index':node_index})
        if result_xpath_lists[key] == []:
            result_xpath_lists[key] = [{'xpath':value.get('xpath'),'node_index':value.get('node_index')} for value in
                                       object_xpath.xpath_lists[key]]
    logger.info(f'寻找xapth耗时：{time.time() - start_time}')
    return result_xpath_lists

def auto_get_json(web_datas, headers, cookies, proxies, xpath_list):
    object_json = Get_json_class()
    object_json.headers = headers
    object_json.cookies = cookies
    object_json.proxies = proxies
    start_time = time.time()
    check_items = web_datas
    for find_item in web_datas:
        object_json.check_items = []
        for check_item in check_items:
            if find_item['url'] != check_item.get('url'):
                object_json.check_items.append(check_item)
        base_url = find_item['url']
        source = find_item.get('dom_source')
        if source:
            # logger.info(find_item['url'])
            # for id in ['itemid']:
            #     if object_json.json_lists[id] == [] and find_item.get(id):
            #         logger.info(f'寻找{id} json')
            #         object_json.get_json(source, find_item.get(id), id)
            for id in ['title', 'brand', 'itemid', 'price', 'cur_price', 'ori_price', 'img', 'breadlist', 'category', 'skuid']:
                if object_json.json_lists[id] == [] and xpath_list.get(id, []) == [] and find_item.get(id):
                    logger.info(f'寻找{id} json')
                    try:
                        object_json.get_json(source, find_item.get(id), id)
                    except func_timeout.exceptions.FunctionTimedOut:
                        logger.info(f'寻找{id} json超时')
            for id in ['img_download']:
                if object_json.json_lists['img'] == [] and xpath_list.get('img', []) == [] and find_item.get(id):
                    base_img_url = find_item.get('img')
                    logger.info(f'寻找{id} json')
                    try:
                        object_json.get_json_img(source, find_item.get(id), id, base_url, base_img_url)
                    except func_timeout.exceptions.FunctionTimedOut:
                        logger.info(f'寻找{id} json超时')

    logger.info(f'寻找json耗时：{time.time() - start_time}')
    return object_json.json_lists

def get_auto_parse_info(auto_parse_info_path, web_datas, headers, cookies, proxies):
    web_datas = deal_web_datas(web_datas, headers, cookies, proxies)
    is_success = True
    for web_data in web_datas:
        is_success = bool(web_data.get('source'))
        if is_success == False:
            break
    if is_success == True:
        new_xpath_list = auto_get_xpath(web_datas, headers, cookies, proxies)
        logger.info(f'新获取xpath: {new_xpath_list}')
        new_json_list = auto_get_json(web_datas, headers, cookies, proxies, new_xpath_list)
        logger.info(f'新获取json: {new_json_list}')
    else:
        logger.info(f'请求存在失败，取用旧解析数据')
        new_xpath_list = auto_get_xpath([], headers, cookies, proxies)
        new_json_list = auto_get_json([], headers, cookies, proxies, new_xpath_list)
    if os.path.exists(auto_parse_info_path):
        logger.info(f'已存在解析数据')
        old_xpath_list, old_json_list = get_old_parse_info(auto_parse_info_path)
        # with open(auto_parse_info_path, 'r', encoding='UTF-8') as f:
        #     try:
        #         old_auto_parse_info = json.load(f)
        #     except:
        #         old_auto_parse_info = {}
        # old_xpath_list = old_auto_parse_info.get('xpath_list', {})
        # old_json_list = old_auto_parse_info.get('json_list', {})
        for key in new_xpath_list.keys():
            if new_xpath_list[key] == []:
                new_xpath_list[key] = old_xpath_list.get(key, [])
        for key in new_json_list.keys():
            if new_json_list[key] == []:
                new_json_list[key] = old_json_list.get(key, [])
    else:
        logger.info(f'未发现已存在解析数据')
    new_auto_parse_info = {
        'xpath_list': new_xpath_list,
        'json_list': new_json_list
    }
    new_auto_parse_info = json.dumps(new_auto_parse_info, indent=4)
    with open(auto_parse_info_path, 'w') as json_file:
        json_file.write(new_auto_parse_info)
    logger.info(f'合并后xpath: {new_xpath_list}')
    logger.info(f'合并后json: {new_json_list}')
    return new_xpath_list, new_json_list


# if __name__ == '__main__':
#     """
#     最终获取xpath形式为
#     {xpath:[node_index]}
#     node_index为xpath获取的node的下标
#     """
#     proxies = {
#     'http': '127.0.0.1:7890',
#     'https': '127.0.0.1:7890',
#     }
#
#     headers = {
#         "authority": "www.sunglasshut.com",
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
#         "cache-control": "max-age=0",
#         "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
#         "sec-ch-ua-mobile": "?0",
#         "sec-ch-ua-platform": "\"Windows\"",
#         "sec-fetch-dest": "document",
#         "sec-fetch-mode": "navigate",
#         "sec-fetch-site": "none",
#         "sec-fetch-user": "?1",
#         "upgrade-insecure-requests": "1",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     }
#     cookies = {
#         "tealium_data2track_Content_TestVersion": "DC-CS:Control|SGH-23-15:Control|SITEWIDE-User-History-Tracker_1665345:Experiment",
#         "mt.v": "2.334308863.1706254097790",
#         "_ALGOLIA": "anonymous-56ce1969-6c38-4483-85e8-15cee8d8102f",
#         "ftr_ncd": "6",
#         "SGPF": "34TxaMbQhnGj_v3TLEbUEZLnXelea-DmxYSvMPEnO7-2n70aCVMtwLg",
#         "utag_main_vapi_domain": "sunglasshut.com",
#         "s_ecid": "MCMID%7C69900897297566516400508435614249580586",
#         "__idcontext": "eyJjb29raWVJRCI6IjJiVHZFVE5VS1c1Mm1JeWtNaFpSZGE4RHB2YiIsImRldmljZUlEIjoiMmJUdkVZU21jM3RRRm0zbnZzMnZlVThORnpvIiwiaXYiOiIiLCJ2IjoiIn0%3D",
#         "CONSENTMGR": "consent:true%7Cts:1706254146670",
#         "_cs_c": "1",
#         "_gcl_au": "1.1.551519772.1706254152",
#         "_pin_unauth": "dWlkPU1XUTBNemxtWWpRdE9ERm1aUzAwTURRNUxXRmxZek10TXpreU1EZ3laR0l5TUdKbQ",
#         "cjConsent": "MHxOfDB8Tnww",
#         "cjUser": "7b9ce5fd-8ef5-4ff8-bb73-fdc53f907b02",
#         "cjLiveRampLastCall": "2024-01-26T07:29:14.839Z",
#         "_scid": "41eb764b-cbcc-4a20-aee1-3db14ef5761a",
#         "__pdst": "5deb26f904cb449da5f2c072ba6423ec",
#         "_tt_enable_cookie": "1",
#         "_ttp": "MKJSwpXKeYBz2DDrsib0iUs1J4n",
#         "_fbp": "fb.1.1706254158828.791755756",
#         "smc_uid": "1706254159736550",
#         "smc_tag": "eyJpZCI6Njc4LCJuYW1lIjoic3VuZ2xhc3NodXQuY29tIn0=",
#         "smc_refresh": "32434",
#         "smc_not": "default",
#         "_ga_PTD50WTZKS": "GS1.2.1706254261.1.0.1706254261.0.0.0",
#         "_ga": "GA1.1.1587734684.1706254153",
#         "cto_bundle": "hc4r_l9xTFZIeVlCMThmVXQlMkY0TVl1OWVwNE5LSnR0ZmdSOHV0eFVFT0wlMkJxbHVjSG4xV3FSa0R0VmxSUCUyQmROQ0oxJTJGMmhBbjFMc1EyTEpOWW92JTJGVnNYbzFOWWJNQW9WalVMeHFiVGxBM01CTUZVRDl4Z1lqQ2E2ZnJCMHR5cnBYWVlRZmlUem5VVHdkQjJSdUdjWWRZME1Zb3h2aFolMkY4Tmpzbk9UMkhiNzRRc2pvJTJCbyUzRA",
#         "_scid_r": "41eb764b-cbcc-4a20-aee1-3db14ef5761a",
#         "_uetvid": "9b653590bc1c11ee9ae069a4d60ab796",
#         "smc_tpv": "3",
#         "smc_sesn": "2",
#         "_ga_6P80B86QTY": "GS1.1.1706254152.1.1.1706254889.60.0.0",
#         "aka-cc": "US",
#         "aka-ct": "LOSANGELES",
#         "aka-zp": "90001-90068+90070-90084+90086-90089+90091+90093-90096+90099+90189",
#         "_abck": "EF148810C995F9789623232EEBC00408~0~YAAQJgwtF7zg7muNAQAAxz/Bcgti01ovoB8wL5W11nH97bzUpfGR/W61wMJmJDbfDhWOsAKJvO3Oi/DRwe/sLsjI5z3Dm50zgMbl3BOeBxCZRGesCGrWJc54OltYkNct8CTAvCKgw0u8sCgxZVt98F9p/AjZIur+hWRdQiVfK8A9eI4G1hZo/+Ou+Ge5mQl5ypTVUpGHv2acopN9jaNTyqDaYHsc2Snb/tdvm3zbA2eBcTvQPmL2hcPtq1bBfaUI5+Nik5v1jJTxW6FtIn8QDzaYautBOEFFmhsY/fUzSEhgbGOKY4xC7ToCH7WFLo5OfRtF795aguA6KOmqGakEpXnjWB3A37Ci6nyVLGCI1uDOau1bd3rhxepc4qbDEg66E91EPQ7HgVkeBA+YcH2nLU7nzzSjM3lVB1ZDyapvIX01LYLpLx3NHqFxz4++KqBU9Wtj9AKhPtPrcAq/cJQ=~-1~-1~-1",
#         "hasVisitedPLP": "true",
#         "rxVisitor": "1707027286574TAPU4K3G1G4VBDSMA3KRN58BOS4657D0",
#         "__wid": "348611435",
#         "ftr_blst_1h": "1707027287238",
#         "dtSa": "-",
#         "sgh-desktop-facet-state-search": "",
#         "cacheBustKey": "1707027424458",
#         "tealium_data2track_Tags_AdobeAnalytics_TrafficSourceJid_ThisHit": "402041REF",
#         "tealium_data_tags_adobeAnalytics_trafficSourceJid_stackingInSession": "402041REF",
#         "tealium_data2track_Tags_AdobeAnalytics_TrafficSourceMid_ThisHit": "v06a0nuzmtf.feishu.cn/",
#         "tealium_data_tags_adobeAnalytics_trafficSourceMid_thisSession": "v06a0nuzmtf.feishu.cn/",
#         "utag_main_v_id": "018d72c16163001464ddc58ff7fa0506f003b06700bd0",
#         "utag_main__sn": "2",
#         "utag_main_ses_id": "1707027292516%3Bexp-session",
#         "tealium_data_session_timeStamp": "1707027292530",
#         "TrafficSource_Override": "1",
#         "tiktok_click_id": "undefined",
#         "_cs_mk_aa": "0.6212146750124743_1707027292557",
#         "utag_main_dc_visit": "2",
#         "utag_main__ss": "0%3Bexp-session",
#         "AMCVS_125138B3527845350A490D4C%40AdobeOrg": "1",
#         "AMCV_125138B3527845350A490D4C%40AdobeOrg": "-1303530583%7CMCIDTS%7C19758%7CMCMID%7C69900897297566516400508435614249580586%7CMCAAMLH-1707632093%7C9%7CMCAAMB-1707632093%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1707034493s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C3.3.0",
#         "s_cc": "true",
#         "utag_main_dc_region": "ap-east-1%3Bexp-session",
#         "sf_siterefer": "salesfloor",
#         "sf_wdt_customer_id": "4twfo9lm3",
#         "sf_wdt_fingerprint": "13627605174699",
#         "dtCookie": "v_4_srv_8_sn_DF0V9SFKLCDDADVB8PQFPS799SFKPSTE_app-3Ab359c07662f0b428_1_ol_0_perc_100000_mul_1",
#         "JSESSIONID": "0000KLOXkGVmLeYKlcLGHFGyc9A:1c7qtqjbr",
#         "TS011f624f": "015966d29264078d4368345907600d597b8b58bc31fded8b578a0257918fd8200ee5b16b2807c96ee32a59593c389ed58396557f23f0b56790272a25cadd9bc3578665b0f7",
#         "tealium_data_action_lastEvent": "click [bx-close-inside-2384706][closeemailsignupdialog]",
#         "s_fid": "48EE8699EB67F1F3-1405AE421F484945",
#         "bm_mi": "350C5593A3B2B2BEA449BEEC65788F79~YAAQJgwtF+f57muNAQAAq2PDchYuJ3cV1sH2y8JKnsgW1o/Oo6O5a+gdOYe+kGoPxMbCMYcpUodeVX0nRB8Gc4Yh/XdRuuzd+oGed7rUFog+6APfRZ9xCULtQJGY24lCixbihaOuOWfukzUsnHiGDMnLElJXSDyHNv0zwtzRqQBfVHNgiAbkUahIZx7TWp4GNkUS8YQPdeA0QHqH6CpJ8DQRDcYxJm6eqUPm/TqNLOYNxWJ3mI9APwaGhO4+BSLM58veOb13lx7PBmTUynAMFWbYGlYrYx0nPf5o80kENRV9FJOLnxt/M3XIyJKTmC8N1qrhPrWAqQoFL4gQOZT6GHy/iA8f3Zpxb2lYcTvAxrAR~1",
#         "bm_sz": "AB61A197A0A3D1EEEC89EF6C3E938EFC~YAAQJgwtF+n57muNAQAAq2PDchYydk2zwNaWvo+aj/F2iL29DKBEoA+8VEUwsDkyFldwOdSnJnq0Qg60+1V2uZ2quyJIaP8I+opyuuaAKk1o3VEYK+TDZgE7tKHF0A4a1J1BOvGhgtxhIzKXk8ciTqMeJu6oqKoqPlGuyFF3JvbHVALe33QO7RQjLsqv6tLUmgZoLDQafNQwjAxUjrPFNVVf/qaVT9y9Ctp6HFfAU8NCx0ItdlPBHJQOzNDxP3T6X2EGF8+1knN0vIhJ9iKiwUu6Iyo1kl0i6dV0UQNPXd7lYvv5oY+Jw38CrzXUBsO4dVl8PhsWPrbKOLmq4aAN/wpON7EocRvJvmpCTg8BYF+n5MPQKqEWnuLXsPm84oay9pt4ETEY3pE=~3618628~3360323",
#         "sf_change_page": "true",
#         "recentlyViewedUS": "3074457345618647096%2C3074457345618602833",
#         "sgh-desktop-facet-state-plp": "categoryid:undefined|gender:true|brands:partial|polarized:true|price:true|frame-shape:partial|color:true|face-shape:false|fit:false|materials:false|lens-treatment:false",
#         "forterToken": "5ea9d7ece0a54e1ebb4f1b6a9a5f7bdc_1707027424967__UDF43-m4_6",
#         "utag_main__pn": "2%3Bexp-session",
#         "tealium_data_action_lastAction": "Rayban:Rb0840s:Pdp-Premium",
#         "s_sq": "%5B%5BB%5D%5D",
#         "utag_main_dc_event": "2%3Bexp-session",
#         "sf_wdt_session_expiration_session": "1707027426951",
#         "_cs_id": "6c66bdb8-a9d5-aa64-d447-bb4084183d56.1706254150.2.1707027427.1707027293.1.1740418150181.1",
#         "_cs_s": "2.0.0.1707029227403",
#         "UserTrackingProducts": "6",
#         "ak_bmsc": "54303BD4AECD06813F11B83E094C207C~000000000000000000000000000000~YAAQJgwtF3D67muNAQAA3HPDchZWmFWXJ8AwyxvAGkj3JaJsGegqGmjHfdMuswGUhonEzpijxOFA7M9US12kHuUfLeXMUDNd7jnCUfaJXv7IRpLtdu3uflRuyi2/Op25LysWxw9ii6qrI3KaWNqCyq5zYLaHIV67z6LUTO81rofRDMQRLByWEHhP16ZSOEYqu1v8PyC0vV+oeEiADRQmgGHDEJKaR+d0hEt9Sl9eaBMihOv3BAIpSGZKJ4pQnW4CZWXIp7v/M+Ag1f1caLNQMVSHRBQ8tDJNQ7IVOXubycrH7WbnVeWWc4n7C1X2SEnpDsmAVRYwGFKBrYLsOdiC4CYivNCVebFg2Yy/YFbra88fOi5KfZ074b+izB8bIgGXjoMOTFSWmg101mGAmFxepvqe02m7n4GY9UnC7G0GY76lf2fMcY6JxSW4hmKSDyb8uSQ07P3fbvGoMD+XsMTshRk9xH9pa5teTk6DMFxhdt96pYoBCXaWSSfUu4rYV6WaZCjpT6DVHtPibeM3zkzU4mCBXsHFNxmpfayvcO/RAcZWaLKgkzJPGRiEfP2y3jwoWCafqUcWxAIUbGI=",
#         "rxvt": "1707029229886|1707027286575",
#         "dtPC": "8$27424977_12h-vFQDTFPPMSRIULPIPWUAAEEHPEPKRVERA-0e0",
#         "bm_sv": "440F5240898C6125427D34369674BE1A~YAAQJgwtF8P67muNAQAAZXrDchaDGf9BeG1QvhD3hveHGZIxLBP8IMwaqyqGXawbt/xazHk06rB2i12fkCgkpLpRaPhyO1s4ybA3d1YlwjLQ0TH7zWdjQPUElWgyJ2kh+w3UzWh+zlWq6vDhRWrEEilOLgnGsap7tfcHfVUWqGwR1zqYhjF5mCThEwBK24ZQwq1JWSm/2GfN0tzyeifBeBaZg9l1mCdK5jkivNOGUNPNAUxjYgG6rRbcgitcQcD/U7pEI9U=~1",
#         "utag_main__se": "9%3Bexp-session",
#         "utag_main__st": "1707029235906%3Bexp-session"
#     }
#     # 从xpath中提取分类信息;从json中提取list形式分类信息使用breadlist
#     # 从json中提取str形式分类信息使用category
#     web_datas = [
#     {
#         "url": "https://www.sunglasshut.com/us/ray-ban/rb0840s-8056597856393",
#         "title": "RB0840S Mega Wayfarer Bio-Based",
#         "cur_price": "182.00",
#         "ori_price": "",
#         "img": "https://assets.sunglasshut.com/is/image/LuxotticaRetail/8056597856393__STD__shad__qt.png?impolicy=SGH_bgtransparent",
#         "breadlist": [
#             'Ray-Ban',
#             'RB0840S Mega Wayfarer Bio-Based'
#         ],
#         'category': 'RB0840S Mega Wayfarer Bio-Based',
#         "brand": "Ray-Ban",
#         'itemid':'8056597856393'
#     },
#     {
#         "url": "https://www.sunglasshut.com/us/persol/po3235s-8056597971409",
#         "title": "PO3235S",
#         "cur_price": "335.00",
#         "ori_price": "",
#         "img": "https://assets.sunglasshut.com/is/image/LuxotticaRetail/8056597971409__STD__shad__qt.png?impolicy=SGH_bgtransparent",
#         "breadlist": [
#             'Persol',
#             'PO3235S'
#         ],
#         'category': 'PO3235S',
#         "brand": "PERSOL",
#         'itemid': '8056597971409'
#     },
#     {
#         "url": "https://www.sunglasshut.com/us/versace/ve4454-8056597921947",
#         "title": "VE4454",
#         "cur_price": "372.00",
#         "ori_price": "",
#         "img": "https://assets.sunglasshut.com/is/image/LuxotticaRetail/8056597921947__STD__shad__qt.png?impolicy=SGH_bgtransparent",
#         "breadlist": [
#             'Versace',
#             'VE4454'
#         ],
#         'category': 'VE4454',
#         "brand": "VERSACE",
#         'itemid': '8056597921947'
#     },
#     {
#         "url": "https://www.sunglasshut.com/us/oakley/oo9154-888392486677",
#         "title": "OO9154 Half Jacket® 2.0 XL",
#         "cur_price": "206.00",
#         "ori_price": "",
#         "img": "https://assets.sunglasshut.com/is/image/LuxotticaRetail/888392486677__STD__shad__qt.png?impolicy=SGH_bgtransparent",
#         "breadlist": [
#             'Oakley',
#             'OO9154 Half Jacket® 2.0 XL'
#         ],
#         'category': 'OO9154 Half Jacket® 2.0 XL',
#         "brand": "Oakley",
#         'itemid': '888392486677'
#     },
#     {
#         "url": "https://www.sunglasshut.com/us/burberry/be4291-8056597787246",
#         "title": "BE4291",
#         "cur_price": "281.00",
#         "ori_price": "",
#         "img": "https://assets.sunglasshut.com/is/image/LuxotticaRetail/8056597787246__STD__shad__qt.png?impolicy=SGH_bgtransparent",
#         "breadlist": [
#             'Burberry',
#             'BE4291'
#         ],
#         'category': 'BE4291',
#         "brand": "Burberry",
#         'itemid': '8056597787246'
#     }
# ]
#     web_datas = deal_web_datas(web_datas, headers, cookies, proxies)
#     start_time = time.time()
#     xpath_list = auto_get_xpath(web_datas, headers, cookies, proxies)
#     print(xpath_list)
#     # xpath_list = {'title': [],'price': [],'ori_price': [],'cur_price': [],'img': [],'brand': [],'breadlist': [],'itemid': []}
#     json_list = auto_get_json(web_datas, headers, cookies, proxies, xpath_list)
#     print(json_list)
#     check_urls = [
#         'https://www.sunglasshut.com/us/ray-ban/rb2197-8056597625869',
#         'https://www.sunglasshut.com/us/prada/pr-58ys-8056597629553'
#     ]
#     for check_url in check_urls:
#         result = {}
#         result['url'] = check_url
#         response = requests.get(check_url, headers=headers, cookies=cookies, proxies=proxies)
#         response = Selector(text=response.text)
#         result['title'] = get_info_from_xpath(xpath_list, response,'title') if xpath_list['title'] else get_info_from_json(json_list, response,'title')
#         result['brand'] = get_info_from_xpath(xpath_list, response, 'brand') if xpath_list['brand'] else get_info_from_json(json_list, response,'brand')
#         price = get_info_from_xpath(xpath_list, response, 'price') if xpath_list['price'] else get_info_from_json(json_list, response,'price')
#         cur_price = get_info_from_xpath(xpath_list, response, 'cur_price') if xpath_list['cur_price'] else get_info_from_json(json_list, response,'cur_price')
#         ori_price = get_info_from_xpath(xpath_list, response, 'ori_price') if xpath_list['ori_price'] else get_info_from_json(json_list, response,'ori_price')
#         result['breadlist'] = get_info_from_xpath(xpath_list, response, 'breadlist') if xpath_list['breadlist'] else get_info_from_json(json_list, response,'breadlist')
#         if not result['breadlist']:
#             result['breadlist'] = get_info_from_json(json_list, response,'category')
#         result['img'] = get_info_from_xpath(xpath_list, response, 'img') if xpath_list['img'] else get_info_from_json(json_list, response,'img')
#         result['itemid'] = get_info_from_xpath(xpath_list, response, 'itemid') if xpath_list['itemid'] else get_info_from_json(json_list, response,'itemid')
#         result['cur_price'] = cur_price if cur_price else price
#         result['ori_price'] = ori_price
#         if ori_price and ori_price == result['cur_price']:
#             result['cur_price'] = None
#         print(result)
