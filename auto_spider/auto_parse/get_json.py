import re
import requests
from urllib.parse import urljoin
from func_timeout import func_set_timeout
from PIL import Image
from io import BytesIO
from auto_parse.setting import check_xpath_wrong, check_xpath_success, check_xpath_fail, find_img_download_timeout, \
    jsonx_xpath_keys, find_timeout
from auto_parse.tools import get_json_lists, filter_html_label, deal_price, deal_img, split_img, sort_img, judge_img, img_similar

class Get_json_class():

    def __init__(self):
        self.json_lists ={
            'title':[],
            'brand':[],
            'itemid':[],
            'skuid':[],
            'price':[],
            'ori_price': [],
            'cur_price': [],
            'img': [],
            'breadlist': [],
            'category': []
        }
        self.check_items = []
        self.img_download_dict = {}
        self.img_score_dict = {}
        self.node_stop = False

        self.headers = {}
        self.cookies = {}
        self.proxies = {}
        self.timeout = 10

    @func_set_timeout(find_timeout)
    def get_json(self, source, data_info, id):
        if id == 'breadlist':
            data_info = data_info[0]
        json_nodes_infos = []
        for node in source.xpath("//*"):
            node_text = ' '.join(node.xpath('./text()'))
            node_json_lists = get_json_lists(node_text)
            node_json_index = 0
            for node_json in node_json_lists:
                for node_json_key, node_json_value in node_json.items():
                    node_json_value = str(node_json_value)
                    find_text = filter_html_label(node_json_value)
                    if id in ['title', 'brand', 'itemid', 'breadlist', 'category', 'skuid']:
                        if find_text.lower() == data_info.lower():
                            json_nodes_infos.append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key})
                    elif id in ['price', 'cur_price', 'ori_price']:
                        if len(find_text) < 50:
                            data_info = deal_price(data_info)
                            find_price = deal_price(find_text)
                            if data_info and find_price and float(data_info) == float(find_price):
                                json_nodes_infos.append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key, 'divide_flag':None})
                            if data_info and find_price and float(data_info) == float(find_price) / 100:
                                json_nodes_infos.append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key, 'divide_flag':100})
                    elif id in ['img']:
                        find_imgs = split_img(node_json_value)
                        find_imgs = [deal_img(i).lower() for i in find_imgs if i]
                        data_info = deal_img(data_info).lower()
                        if find_imgs and data_info in find_imgs:
                            json_nodes_infos.append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key})

                node_json_index = node_json_index + 1

        for json_nodes_info in json_nodes_infos:
            json_node = json_nodes_info.get('json_node')
            json_index = json_nodes_info.get('json_index')
            json_key = json_nodes_info.get('json_key')
            divide_flag = json_nodes_info.get('divide_flag')
            json_node_full_xpath = self.get_json_node_full_xpath(json_node, None, source)
            find_nodes = source.xpath(json_node_full_xpath)
            for json_node_index in range(len(find_nodes)):
                if find_nodes[json_node_index] == json_node:
                    json_node_full_xpath = json_node_full_xpath + f'/text()'
                    break
            success_num = 0
            wrong_num = 0
            for check_item in self.check_items:
                check_item_source = check_item.get('dom_source')
                if check_item_source:
                    json_item = {'json_xpath':json_node_full_xpath, 'json_node_index':json_node_index, 'json_index':json_index, 'json_key':json_key, 'divide_flag':divide_flag}
                    check_result = self.check_json(check_item_source, json_item, check_item, id)
                    if check_result == check_xpath_success:
                        success_num = success_num + 1
                    if check_result == check_xpath_wrong:
                        wrong_num = wrong_num + 1
                        break
            if wrong_num == 0 and success_num > 0:
                self.json_lists[id] = self.json_lists[id] + [{'json_xpath':json_node_full_xpath, 'json_node_index':json_node_index, 'json_index':json_index, 'json_key':json_key, 'divide_flag':divide_flag}]
                break

    @func_set_timeout(find_img_download_timeout)
    def get_json_img(self, source, data_info, id, base_url, base_img_url):
        all_imgs = {}
        for node in source.xpath("//*"):
            node_text = ' '.join(node.xpath('./text()'))
            node_json_lists = get_json_lists(node_text)
            node_json_index = 0
            for node_json in node_json_lists:
                for node_json_key, node_json_value in node_json.items():
                    node_json_value = str(node_json_value)
                    node_img = judge_img(node_json_value, json_key=node_json_key)
                    if node_img:
                        if node_img.startswith('http') == False:
                            if node_img.startswith('//'):
                                node_img = urljoin(base_url, node_img)
                            else:
                                node_img = urljoin(base_url, '/' + node_img.lstrip('/'))
                        if node_img in all_imgs.keys():
                            all_imgs[node_img].append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key})
                        else:
                            all_imgs[node_img] = []
                            all_imgs[node_img].append({'json_node':node, 'json_index':node_json_index, 'json_key':node_json_key})
                node_json_index = node_json_index + 1

        sort_all_imgs_keys = sort_img(list(all_imgs.keys()), base_img_url)

        for key in sort_all_imgs_keys:
            if self.json_lists['img'] != []:
                break
            value = all_imgs[key]
            find_img = key
            true_img_content = data_info
            try:
                if find_img not in self.img_download_dict.keys():
                    find_img_content = requests.get(find_img, timeout=self.timeout, headers=self.headers, stream=True, cookies=self.cookies, proxies=self.proxies)
                    self.img_download_dict[find_img] = find_img_content
                else:
                    find_img_content = self.img_download_dict[find_img]
                w = Image.open(BytesIO(find_img_content.content)).size[0]
                h = Image.open(BytesIO(find_img_content.content)).size[1]
            except:
                w = 0
                h = 0
            if w * h > 350 * 350:
                try:
                    if true_img_content.url + find_img_content.url not in self.img_score_dict.keys():
                        score_rough = img_similar(true_img_content, find_img_content)
                        self.img_score_dict[true_img_content.url + find_img_content.url] = score_rough
                    else:
                        score_rough = self.img_score_dict[true_img_content.url + find_img_content.url]
                except:
                    score_rough = 0
                if score_rough > 0.9:
                    for node in value:
                        if self.json_lists['img'] != []:
                            break
                        json_node = node.get('json_node')
                        json_index = node.get('json_index')
                        json_key = node.get('json_key')
                        json_node_full_xpath = self.get_json_node_full_xpath(json_node, None, source)
                        find_nodes = source.xpath(json_node_full_xpath)
                        for json_node_index in range(len(find_nodes)):
                            if find_nodes[json_node_index] == json_node:
                                json_node_full_xpath = json_node_full_xpath + '/text()'
                                break
                        success_num = 0
                        wrong_num = 0
                        for check_item in self.check_items:
                            check_item_source = check_item.get('dom_source')
                            if check_item_source:
                                json_item = {'json_xpath': json_node_full_xpath, 'json_node_index':json_node_index, 'json_index': json_index, 'json_key': json_key}
                                check_result = self.check_json(check_item_source, json_item, check_item, id)
                                if check_result == check_xpath_success:
                                    success_num = success_num + 1
                                if check_result == check_xpath_wrong:
                                    wrong_num = wrong_num + 1
                                    break
                        if wrong_num == 0 and success_num > 0:
                            self.json_lists['img'] = self.json_lists['img'] + [{'json_xpath': json_node_full_xpath, 'json_node_index':json_node_index, 'json_index': json_index, 'json_key': json_key}]
                            break

    def get_json_node_full_xpath(self, json_node, base_xpath, source):
        if base_xpath == None:
            base_xpath = "//" + json_node.tag
            for jsonx_xpath_key in jsonx_xpath_keys:
                if jsonx_xpath_key in json_node.attrib.keys():
                    json_xpath_value = json_node.attrib.get(jsonx_xpath_key)
                    if json_xpath_value:
                        base_xpath = base_xpath + f'[@{jsonx_xpath_key}="{json_xpath_value}"]'
                        break
        full_xpath = base_xpath
        num_count = len(source.xpath(full_xpath))
        if num_count == 1:
            pass
        else:
            parent_nodes = json_node.xpath('./parent::*')
            if parent_nodes:
                parent_node = parent_nodes[0]
                if parent_node.tag == 'head' or parent_node.tag == 'body' or parent_node.tag == 'html':
                    pass
                else:
                    parent_xpath = "//" + parent_node.tag + base_xpath[1:]
                    full_xpath = self.get_json_node_full_xpath(parent_node, parent_xpath, source)
        return full_xpath

    def check_json(self, check_item_source, json_item, check_item, id):
        check_result = None
        check_info = None
        json_xpath = json_item.get('json_xpath')
        json_node_xpath = '/'.join(json_xpath.split('/')[0:-1])
        json_node_info_xpath = './'+json_xpath.split('/')[-1]
        json_node_index = json_item.get('json_node_index')
        json_index = json_item.get('json_index')
        json_key = json_item.get('json_key')
        divide_flag = json_item.get('divide_flag')
        json_node_result = check_item_source.xpath(json_node_xpath)
        if len(json_node_result) > json_node_index:
            json_texts = ' '.join(json_node_result[json_node_index].xpath(json_node_info_xpath))
            check_jsons = get_json_lists(json_texts)
            if len(check_jsons) > json_index:
                check_json = check_jsons[json_index]
                check_info = check_json.get(json_key)
        if id in ['title', 'brand', 'itemid', 'category', 'skuid']:
            if not check_item.get(id):
                return
            if not check_info:
                check_result = check_xpath_wrong
                return check_result
            result_text = filter_html_label(check_info)
            if result_text.lower() == check_item.get(id).lower():
                check_result = check_xpath_success
            else:
                check_result = check_xpath_wrong
        elif id in ['price','cur_price','ori_price']:
            if check_item.get(id):
                if not check_info:
                    check_result = check_xpath_wrong
                    return check_result
                true_price = deal_price(check_item[id])
                check_price = deal_price(check_info)
                if divide_flag != None:
                    check_price = float(check_price) / divide_flag
                if true_price and check_price and float(true_price) == float(check_price):
                    check_result = check_xpath_success
                else:
                    check_result = check_xpath_wrong
            else:
                if not check_info:
                    return
                check_price = deal_price(check_info)
                if divide_flag != None:
                    check_price = float(check_price) / divide_flag
                if id in ['price']:
                    true_ori_price = deal_price(check_item['ori_price'])
                    true_cur_price = deal_price(check_item['cur_price'])
                    if check_price and float(check_price) != float(true_ori_price) and float(check_price) != float(true_cur_price):
                        check_result = check_xpath_wrong
                elif id in ['ori_price', 'cur_price']:
                    true_price = deal_price(check_item['price'])
                    if check_price and float(check_price) != float(true_price):
                        check_result = check_xpath_wrong
        elif id in ['img']:
            if not check_item.get(id):
                return
            if not check_info:
                check_result = check_xpath_wrong
                return check_result
            check_imgs = split_img(check_info)
            check_imgs = [deal_img(i).lower() for i in check_imgs if i]
            true_img = deal_img(check_item[id]).lower()
            if check_imgs and true_img in check_imgs:
                check_result = check_xpath_success
            else:
                check_result = check_xpath_wrong
        elif id in ['img_download']:
            if not check_item.get(id):
                return
            if not check_info:
                check_result = check_xpath_wrong
                return check_result
            check_img = split_img(check_info)[-1] if split_img(check_info) else ''
            if check_img.startswith('http') == False:
                if check_img.startswith('//'):
                    check_img = urljoin(check_item['url'], check_img)
                else:
                    check_img = urljoin(check_item['url'], '/' + check_img.lstrip('/'))
            try:
                true_img_content = check_item.get(id)
                if check_img not in self.img_download_dict.keys():
                    check_img_content = requests.get(check_img, timeout=self.timeout, headers=self.headers, stream=True, cookies=self.cookies, proxies=self.proxies)
                    self.img_download_dict[check_img] = check_img_content
                else:
                    check_img_content = self.img_download_dict[check_img]
                if true_img_content.url + check_img_content.url not in self.img_score_dict.keys():
                    score = img_similar(true_img_content, check_img_content)
                    self.img_score_dict[true_img_content.url + check_img_content.url] = score
                else:
                    score = self.img_score_dict[true_img_content.url + check_img_content.url]
                w = Image.open(BytesIO(check_img_content.content)).size[0]
                h = Image.open(BytesIO(check_img_content.content)).size[1]
            except:
                score = 0
                w = 0
                h = 0
            if score > 0.9:
                check_result = check_xpath_success
            else:
                check_result = check_xpath_wrong
        if id in ['breadlist']:
            if not check_item.get(id):
                return
            if not check_info:
                check_result = check_xpath_wrong
                return check_result
            true_text = [filter_html_label(text.lower()) for text in check_item[id]]
            if 'list_index' not in json_key:
                result_text = [filter_html_label(check_info.lower())]
            else:
                result_text = []
                json_keys = json_key.split('>>>')
                for j_k in range(len(json_keys)-1, -1, -1):
                    if 'list_index' in json_keys[j_k]:
                        json_keys[j_k] = 'list_index_\d+'
                        break
                json_key = '>>>'.join(json_keys)
                for check_json_key in check_json.keys():
                    if re.findall(json_key, check_json_key):
                        result_text.append(check_json.get(check_json_key))
                result_text = [filter_html_label(text.lower()) for text in result_text]
            if result_text == true_text:
                check_result = check_xpath_success
            else:
                check_result = check_xpath_wrong

        return check_result