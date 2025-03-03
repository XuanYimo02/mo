#-- coding:UTF-8 --
import json
import os
import re
import logging
from urllib.parse import urljoin, urlsplit
import numpy as np
import price_parser
import html
from PIL import Image
from io import BytesIO
from skimage.metrics import structural_similarity as ssim
from skimage.color import rgb2gray
from skimage import  transform
from auto_parse.setting import img_suffix, img_keys, img_nodes, key_less, json_img_keys, json_img_keys_suffix
logger = logging.getLogger(__name__)

def filter_html_label(text):
    """
    处理字符串
    """
    if text == None:
        return ''
    text = str(text)
    text = ''.join([i for i in text if i.isprintable()])
    if re.search(r'[0-9a-z]', text.lower()) == None:
        try:
            text = text.encode('raw_unicode_escape').decode()
        except:
            pass
    text = html.unescape(text)
    # 注释，js，css
    filter_rerule_list = [r'(<!--[\s\S]*?-->)', r'<script[\s\S]*?</script>', r'<style[\s\S]*?</style>']
    for filter_rerule in filter_rerule_list:
        html_labels = re.findall(filter_rerule, text)
        for h in html_labels:
            text = text.replace(h, ' ')
    filter_char_list = [
        u'\x85', u'\xa0', u'\u1680', u'\u180e', u'\u2000', u'\u200a',u'\u200b', u'\u2028', u'\u2029', u'\u202f', u'\u205f',
        u'\u3000', u'\xA0', u'\u180E', u'\u200A', u'\u202F', u'\u205F', '\t', '\n', '\r', '\f', '\v',
    ]
    for f_char in filter_char_list:
        text = text.replace(f_char, ' ')
    text = re.sub(' +', ' ', text).strip()
    text = text.replace('> <', '><')
    text = text.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
    return text

def deal_price(price):
    """
    从字符串中解析出价格
    """
    price = str(price)
    price = filter_html_label(price)
    try:
        check_price = float(price)
        if str(price_parser.parse_price(price).amount) != 'None':
            return str(price_parser.parse_price(price).amount)
    except:
        check_price = price.replace(',','').replace('.','')
        if check_price.isdigit():
            price = price_parser.parse_price(price)
            price = price.amount
            if str(price) != 'None':
                return str(price)
        else:
            price = price_parser.parse_price(price)
            currency = price.currency
            price = price.amount
            if currency and str(price) != 'None':
                return str(price)
            else:
                return ''

def judge_img(text, key=None, node_name=None, json_key=None):
    """
    判断字符串是否含有图片
    """
    img = None
    for i in img_suffix:
        if i in text.lower():
            text = split_img(text)
            if text:
                img = text[-1]
                break
    if not img and key in img_keys and node_name in img_nodes:
        text = split_img(text)
        if text:
            img = text[-1]
    if not img and json_key and any(j_i_key in json_key for j_i_key in json_img_keys) and any(j_i_key in json_key.split('>>>')[-1] for j_i_key in json_img_keys_suffix):
        text = split_img(text)
        if text:
            img = text[-1]
    return img

def split_img(text):
    """
    从多张图片的字符串中分离出单个图片
    """
    if text == None:
        return []
    text = text.replace('\r', '').replace('\n', '').replace('\t', '').strip()
    if re.findall(r' +\d+w,', text):
        text = re.split(r' +\d+w,', text)
        text = [re.split(r' +\d+w', i)[0].strip() for i in text if i]
    elif re.findall(r' +\d+x,', text):
        text = re.split(r' +\d+x,', text)
        text = [re.split(r' +\d+x', i)[0].strip() for i in text if i]
    if isinstance(text, str):
        text = [text]
    return text

def deal_img(text):
    """
    处理图片字符串
    """
    text = text.strip()
    text = urlsplit(text).path + '?' + urlsplit(text).query if urlsplit(text).query else urlsplit(text).path
    text = html.unescape(text)
    # text = text.split('?')[0]
    # if '.' in text:
    #     text = '.'.join(text.split('.')[0:-1])
    return text

def img_similar(img_1, img_2):
    """
    判断图片相似度
    """
    img1,img_1_size = loadImage(img_1)
    img2,img_2_size = loadImage(img_2)
    if img_1_size < img_2_size:
        score = calucateImagePairSim(img1,img2)
    else:
        score = calucateImagePairSim(img2, img1)
    if score:
        return score[0]
    else:
        return 0

def calucateImagePairSim(img1, img2, thresh=0.95):
    """
    计算2张图片的结构化相似性:
      imgpath1: dom中解析得到的img1, 默认取低分辨率
      imgpath2: weshop商品引擎中保存的imgdata, 默认都是最高分辨率
    """
    img1 = rgb2gray(img1)
    shape = img1.shape[:2]
    img2 = rgb2gray(img2)
    img2 = transform.resize(img2, shape)
    assert img1.shape==img2.shape, "图片分辨率不一致, img1:shape-{}, img2:shape-{}".format(img1.shape, img2.shape)
    simi = ssim(img1, img2, full=True, gaussian_weights=True, data_range=1)
    return simi

def loadImage(imgUrl):
    # 适配webp以及jpeg, png格式加载图片
    # timeout--(建立连接时间, 读取内容超时时间), default: Secs
    # resp = requests.get(imgUrl, stream=True, timeout=(5, 10))
    # 字节流
    resp = imgUrl
    byte_stream = BytesIO(resp.content)
    w = Image.open(byte_stream).size[0]
    h = Image.open(byte_stream).size[1]
    img = Image.open(byte_stream).convert("RGB")
    img = np.array(img)
    return img,w*h

def parse_json(json, json_result={}, path=[]):
    for key,value in json.items():
        if isinstance(value, list):
            index = 0
            for list_value in value:
                json_path = path + [key]
                json_result = parse_json({'list_index_' + str(index) : list_value}, json_result, json_path)
                index = index + 1
        elif isinstance(value, dict):
            json_path = path + [key]
            json_result = parse_json(value, json_result, json_path)
        else:
            json_path = '>>>'.join(path + [key])
            json_result[json_path] = value
    return json_result

def get_json_lists(source):
    # json_source = html.unescape(source)
    json_source = source.replace('\r','').replace('\n','').replace('\t','')
    json_source = re.sub('{ *','{',json_source)
    json_lists, stack = [], []
    for i in range(len(json_source)):
        try:
            if json_source[i] == '{':
                stack.append(i)
            elif json_source[i] == '}':
                begin = stack.pop()
                if not stack:
                    text = json_source[begin:i + 1]
                    try:
                        json_text = json.loads(text)
                        json_lists.append(json_text)
                    except:
                        try:
                            text = '"' + text.strip().strip('"').replace('false','False').replace('true','True').replace('null','None') + '"'
                            json_text = eval(eval(text))
                            if isinstance(json_text, dict):
                                json_lists.append(json_text)
                        except:
                            pass
        except:
            pass
    json_lists = [parse_json(json_info, {}, []) for json_info in json_lists]
    return json_lists

def sort_img(img_lists, base_img_url):
    base_img_url_suffix = urlsplit(base_img_url).path.strip('/').split('/')[-1]
    if '.' in base_img_url_suffix:
        base_img_url_suffix = '.'.join(base_img_url_suffix.split('.')[0:-1])
    sort_all_imgs_keys = []
    for img_key in img_lists:
        img_key_suffix = urlsplit(img_key).path.split('/')[-1]
        if '.' in img_key_suffix:
            img_key_suffix = '.'.join(img_key_suffix.split('.')[0:-1])
        if base_img_url_suffix in img_key or img_key_suffix in base_img_url:
            sort_all_imgs_keys.append(img_key)
    for sort_img in sort_all_imgs_keys:
        img_lists.remove(sort_img)
    sort_all_imgs_keys = sort_all_imgs_keys + img_lists
    return sort_all_imgs_keys

def get_info_from_xpath(xpath_list, response, id):
    xpath_result = None
    try:
        xpath_items = xpath_list.get(id)
        if xpath_items:
            for xpath_item in xpath_items:
                info = None
                node_index = xpath_item.get('node_index')
                node_xpath = '/'.join(xpath_item.get('xpath').split('/')[0:-1])
                info_xpath = './' + xpath_item.get('xpath').split('/')[-1]
                node_result = response.xpath(node_xpath)
                if id in ['title', 'brand', 'itemid', 'category', 'skuid'] and len(node_result) > node_index:
                    info = ' '.join(node_result[int(node_index)].xpath(info_xpath).extract())
                    info = filter_html_label(info)
                elif id in ['img'] and len(node_result) > node_index:
                    info = ' '.join(node_result[int(node_index)].xpath(info_xpath).extract())
                elif id in ['ori_price', 'cur_price', 'price'] and len(node_result) > node_index:
                    info = ' '.join(node_result[int(node_index)].xpath(info_xpath).extract())
                    info = float(price_parser.parse_price(info).amount) if price_parser.parse_price(info).amount else None
                elif id in ['breadlist']:
                    info = []
                    bread_nodes = node_result
                    for bread_node in bread_nodes:
                        bread = ' '.join(bread_node.xpath(info_xpath).extract())
                        bread = filter_html_label(bread)
                        if bread:
                            info.append(bread)
                    info = '/'.join(info)
                if info:
                    xpath_result = info
                    break
    except:
        logger.error(f'xpath提取{id}出错')
    return xpath_result

def get_info_from_json(json_list, response, id):
    json_result = None
    try:
        json_infos = json_list.get(id)
        if json_infos:
            for json_info in json_infos:
                info = None
                json_xpath = json_info.get('json_xpath')
                json_node_xpath = '/'.join(json_xpath.split('/')[0:-1])
                json_node_info_xpath = './' + json_xpath.split('/')[-1]
                json_node_index = json_info.get('json_node_index')
                json_index = json_info.get('json_index')
                json_key = json_info.get('json_key')
                divide_flag = json_info.get('divide_flag')
                json_node_result = response.xpath(json_node_xpath)
                if len(json_node_result) > json_node_index:
                    json_text = ' '.join(json_node_result[json_node_index].xpath(json_node_info_xpath).extract())
                    jsons = get_json_lists(json_text)
                    if len(jsons) > json_index:
                        json = jsons[json_index]
                        info = str(json.get(json_key,''))
                        if id in ['title', 'brand', 'itemid', 'category', 'skuid']:
                            info = filter_html_label(info)
                        elif id in ['img']:
                            pass
                        elif id in ['ori_price', 'cur_price', 'price']:
                            info = float(price_parser.parse_price(info).amount) if price_parser.parse_price(info).amount else None
                            if info and divide_flag:
                                info = info / divide_flag
                        elif id in ['breadlist']:
                            if 'list_index' not in json_key:
                                info = filter_html_label(info)
                            else:
                                info = []
                                bread_json_keys = json_key.split('>>>')
                                for j_k in range(len(bread_json_keys) - 1, -1, -1):
                                    if 'list_index' in bread_json_keys[j_k]:
                                        bread_json_keys[j_k] = 'list_index_\d+'
                                        break
                                bread_json_key = '>>>'.join(bread_json_keys)
                                for json_key in json.keys():
                                    if re.findall(bread_json_key, json_key):
                                        bread = json.get(json_key,'')
                                        bread = filter_html_label(bread)
                                        if bread:
                                            info.append(bread)
                                info = '/'.join(info)
                    if info:
                        json_result = info
                        break
    except:
        logger.error(f'json提取{id}出错')
    return json_result

def get_info_from_auto_parse(response, id, xpath_list, json_list):
    info = get_info_from_xpath(xpath_list, response, id) if xpath_list.get(id) and get_info_from_xpath(xpath_list, response, id) else get_info_from_json(json_list, response, id)
    return info

def get_old_parse_info(auto_parse_info_path):
    old_xpath_list = {}
    old_json_list = {}
    if auto_parse_info_path and os.path.exists(auto_parse_info_path):
        with open(auto_parse_info_path, 'r', encoding='UTF-8') as f:
            try:
                old_auto_parse_info = json.load(f)
            except:
                old_auto_parse_info = {}
        old_xpath_list = old_auto_parse_info.get('xpath_list', {})
        old_json_list = old_auto_parse_info.get('json_list', {})
    return old_xpath_list, old_json_list