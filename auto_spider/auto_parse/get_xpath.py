#-- coding:UTF-8 --
# 获取xpath
import json
import re
from urllib.parse import urljoin, urlsplit
import requests
from PIL import Image
from io import BytesIO
from func_timeout import func_set_timeout
from auto_parse.setting import key_less, value_less, check_xpath_fail, check_xpath_success, \
    check_xpath_wrong, check_xpath_continue, find_img_download_timeout, find_timeout
from auto_parse.tools import filter_html_label, deal_price, judge_img, img_similar, split_img, deal_img, sort_img

class Get_xpath_class():

    def __init__(self):
        self.xpath_lists ={
                                'title': [],
                                'price': [],
                                'ori_price': [],
                                'cur_price': [],
                                'img': [],
                                'brand': [],
                                'breadlist': [],
                                'itemid': [],
                                'category': [],
                                'skuid': []
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
    def get_xpath(self, source, data_info, id):
        """
        获取预备节点
        """
        if data_info == None:
            return
        data_info_text_nodes = []
        data_info_len = 1
        if id == 'breadlist':
            data_info_len = len(data_info)
            data_info = data_info[-1]
        data_info = data_info.lower()


        # 从节点的text中寻找
        for node in source.xpath("//*"):
            node_text = ' '.join(node.xpath("./text()"))
            if node_text:
                if len(data_info_text_nodes)<10:
                    if ('{' in node_text and  '};' in node_text) or 'var ' in node_text :
                        continue
                    try:
                        js = json.loads(node_text)
                        if isinstance(js,dict):
                            continue
                    except:
                        pass
                    if id in ['price','ori_price','cur_price']:
                        node_text = filter_html_label(node_text)
                        if len(node_text) < 50:
                            data_info = deal_price(data_info)
                            find_price = deal_price(node_text)
                            if data_info and find_price and float(data_info) == float(find_price):
                                data_info_text_nodes.append(node)
                    elif id in ['title', 'brand', 'breadlist', 'itemid', 'category', 'skuid']:
                        find_text = filter_html_label(node_text)
                        if find_text.lower() == data_info:
                            data_info_text_nodes.append(node)

        for data_info_text_node in data_info_text_nodes:
            self.node_stop = False
            if data_info_text_node.attrib == {}:
                xpath = self.return_xpath(data_info_text_node, None, None, '/text()')
                self.xpath_count(xpath, source, data_info_text_node, id, ori_node=data_info_text_node, data_info_len=data_info_len)
            else:
                sort_node_attrib = self.sort_attrib(data_info_text_node, source)
                for key,value in sort_node_attrib.items():
                    if self.node_stop == False:
                        xpath = self.return_xpath(data_info_text_node, key, value, '/text()')
                        self.xpath_count(xpath, source, data_info_text_node, id, ori_node=data_info_text_node, data_info_len=data_info_len)
                    else:
                        break
                if self.node_stop == False:
                    xpath = self.return_xpath(data_info_text_node, None, None, '/text()')
                    self.xpath_count(xpath, source, data_info_text_node, id, ori_node=data_info_text_node, data_info_len=data_info_len)

        #从标签中寻找
        data_info_value_nodes = []
        for node in source.xpath("//*"):
            for key, value in node.attrib.items():
                if ('{' in value and '};' in value) or 'var ' in value :
                    continue
                try:
                    js = json.loads(value)
                    if isinstance(js, dict):
                        continue
                except:
                    pass
                if value:
                    if id in ['price','ori_price','cur_price']:
                        if len(data_info_value_nodes) < 10:
                            if len(value) < 50:
                                data_info = deal_price(data_info)
                                find_price = deal_price(value)
                                if data_info and find_price and float(data_info) == float(find_price):
                                    data_info_value_nodes.append([node, key])
                        else:
                            break
                    elif id in ['img']:
                        if len(data_info_value_nodes) < 10:
                            find_imgs = split_img(value)
                            find_imgs = [deal_img(i).lower() for i in find_imgs if i]
                            data_info = deal_img(data_info).lower()
                            if find_imgs and data_info in find_imgs:
                                data_info_value_nodes.append([node, key])
                        else:
                            break
                    elif id in ['title', 'brand', 'breadlist', 'itemid', 'category', 'skuid']:
                        if len(data_info_value_nodes) < 10:
                            find_text = filter_html_label(value)
                            if find_text.lower() == data_info.lower():
                                data_info_value_nodes.append([node, key])
                        else:
                            break

        for data_info_value_node in data_info_value_nodes:
            self.node_stop = False
            node_attrib = data_info_value_node[1]
            data_info_value_node = data_info_value_node[0]
            sort_node_attrib = self.sort_attrib(data_info_value_node, source, node_attrib)
            for key, value in sort_node_attrib.items():
                if self.node_stop == False:
                    xpath = self.return_xpath(data_info_value_node, key, value, '/@'+node_attrib)
                    self.xpath_count(xpath, source, data_info_value_node, id, ori_node=data_info_value_node, data_info_len=data_info_len)
                else:
                    break
            if self.node_stop == False:
                xpath = self.return_xpath(data_info_value_node, None, None, '/@'+node_attrib)
                self.xpath_count(xpath, source, data_info_value_node, id, ori_node=data_info_value_node, data_info_len=data_info_len)

    @func_set_timeout(find_img_download_timeout)
    def get_xpath_img(self, source, data_info, id, base_url, base_img_url):
        """
        以图片相似度形式，获取预备节点
        """
        all_imgs = {}
        for node in source.xpath("//*"):
            node_name = node.tag
            for key, value in node.attrib.items():
                if ('{' in value and '};' in value) or 'var ' in value :
                    continue
                try:
                    js = json.loads(value)
                    if isinstance(js, dict):
                        continue
                except:
                    pass
                if value:
                    if '(' not in value.lower() and ')' not in value.lower() and 'pinterest.com' not in value.lower():
                        node_img = judge_img(value, key=key, node_name=node_name)
                        if node_img:
                            if node_img.startswith('http') == False:
                                if node_img.startswith('//'):
                                    node_img = urljoin(base_url, node_img)
                                else:
                                    node_img = urljoin(base_url, '/'+node_img.lstrip('/'))
                            if node_img in all_imgs.keys():
                                all_imgs[node_img].append([node, node_img, key])
                            else:
                                all_imgs[node_img] = []
                                all_imgs[node_img].append([node, node_img, key])

        sort_all_imgs_keys = sort_img(list(all_imgs.keys()), base_img_url)

        # 从标签中寻找
        for key in sort_all_imgs_keys:
            if self.xpath_lists['img'] != []:
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
                    if true_img_content.url+find_img_content.url not in self.img_score_dict.keys():
                        score_rough = img_similar(true_img_content,find_img_content)
                        self.img_score_dict[true_img_content.url+find_img_content.url] = score_rough
                    else:
                        score_rough = self.img_score_dict[true_img_content.url+find_img_content.url]
                except:
                    score_rough = 0
                if score_rough > 0.9:
                    for node in value:
                        if self.xpath_lists['img'] != []:
                            break
                        self.node_stop = False
                        node_attrib = node[2]
                        node = node[0]
                        sort_node_attrib = self.sort_attrib(node, source, node_attrib)
                        for node_key, node_value in sort_node_attrib.items():
                            if self.node_stop == False:
                                xpath = self.return_xpath(node, node_key, node_value, '/@'+node_attrib)
                                self.xpath_count(xpath, source, node, id, ori_node=node)
                            else:
                                break
                        if self.node_stop == False and self.xpath_lists['img'] == []:
                            xpath = self.return_xpath(node, None, None, '/@'+node_attrib)
                            self.xpath_count(xpath, source, node, id, ori_node=node)

    def xpath_count(self, xpath, source, data_info_value_node, id, ori_node='', data_info_len=1):
        """
        检查xpath在当前页面结果数量
        """
        #如果xpath匹配结果数量大于1并且没有找到头，则继续像上寻找
        if xpath == None:
            return
        parent = data_info_value_node.xpath('./parent::*')
        if parent:
            parent = parent[0]
        else:
            parent = ''
        node_xpath = '/'.join(xpath.split('/')[0:-1])
        first_node_xpath = '//' + xpath.split('/')[2]
        result = source.xpath(node_xpath)
        count = len(result)
        first_node_count = len(source.xpath(first_node_xpath))
        check_start = False
        if count == data_info_len:
            if result[data_info_len-1] == ori_node:
                xpath_item  = {
                    'xpath': xpath,
                    'node_index': data_info_len-1,
                    'xpath_type': 1
                }
                check_start = True
        elif count > 1:
            if ((parent.tag == 'head' or parent.tag == 'body' or parent.tag == 'html') and id not in ['breadlist']) or first_node_count == data_info_len:
                for r in range(len(result)):
                    if result[r] == ori_node:
                        xpath_item = {
                            'xpath': xpath,
                            'node_index': r,
                            'xpath_type': 2
                        }
                        check_start = True
                        break
            else:
                self.find_parent(xpath, source, data_info_value_node, id, ori_node=ori_node, data_info_len=data_info_len)
        if check_start:
            success_num = 0
            fail_num = 0
            wrong_num = 0
            continue_num = 0
            for check_item in self.check_items:
                check_item_source = check_item.get('dom_source')
                if check_item_source:
                    check_result = self.check_xpath(check_item_source, xpath_item, check_item, id)
                    if check_result == check_xpath_wrong:
                        wrong_num = wrong_num + 1
                        break
                    elif check_result == check_xpath_success:
                        success_num = success_num + 1
                    elif check_result == check_xpath_fail:
                        fail_num = fail_num + 1
                        if fail_num > 1:
                            break
                    elif check_result == check_xpath_continue:
                        continue_num = continue_num + 1
            if wrong_num > 0:
                self.node_stop = True
                return
            if fail_num < 2 and success_num > 0 and wrong_num == 0 and continue_num == 0:
                self.node_stop = True
                if id == 'img_download':
                    self.xpath_lists['img'] = self.xpath_lists['img'] + [xpath_item]
                else:
                    self.xpath_lists[id] = self.xpath_lists[id] + [xpath_item]
                return
            if continue_num > 0:
                self.find_parent(xpath, source, data_info_value_node, id, ori_node=ori_node, data_info_len=data_info_len)

    def find_parent(self, xpath, source, data_info_value_node, id, ori_node='', data_info_len=1):
        """
        寻找父节点，向上层写xpath
        """
        parent = data_info_value_node.xpath('./parent::*')
        if parent:
            parent = parent[0]
            if parent.tag == 'head' or parent.tag == 'body' or parent.tag == 'html':
                return
            if xpath.count('/') < 7 :
                if parent.attrib == {}:
                    if self.node_stop == False:
                        parent_xpath = self.return_xpath(parent, None, None, xpath[1:])
                        self.xpath_count(parent_xpath, source, parent, id, ori_node=ori_node, data_info_len=data_info_len)
                else:
                    sort_node_attrib = self.sort_attrib(parent, source)
                    for key, value in sort_node_attrib.items():
                        if self.node_stop == False:
                            parent_xpath = self.return_xpath(parent, key, value, xpath[1:])
                            self.xpath_count(parent_xpath, source, parent, id, ori_node=ori_node, data_info_len=data_info_len)
                        else:
                            break
                    if self.node_stop == False:
                        parent_xpath = self.return_xpath(parent, None, None, xpath[1:])
                        self.xpath_count(parent_xpath, source, parent, id, ori_node=ori_node, data_info_len=data_info_len)
            else:
                if (parent.attrib == {} or 'class' not in list(parent.attrib.keys())):
                    if self.node_stop == False:
                        parent_xpath = self.return_xpath(parent, None, None, xpath[1:])
                        self.xpath_count(parent_xpath, source, parent, id, ori_node=ori_node, data_info_len=data_info_len)
                else:
                    if self.node_stop == False:
                        key = 'class'
                        value = parent.attrib.get(key)
                        parent_xpath = self.return_xpath(parent, key, value, xpath[1:])
                        self.xpath_count(parent_xpath, source, parent, id, ori_node=ori_node, data_info_len=data_info_len)

    def check_xpath(self, check_source, check_xpath_item, check_item, id):
        """
        利用其他url，验证xpath是否正确
        """
        check_result = None
        xpath = check_xpath_item.get('xpath')
        index = check_xpath_item.get('node_index')
        node_xpath = '/'.join(xpath.split('/')[0:-1])
        info_xpath = './'+xpath.split('/')[-1]
        result_node = check_source.xpath(node_xpath)
        count = len(result_node)
        if id in ['price','cur_price','ori_price']:
            if check_item.get(id):
                if count == 0:
                    check_result = check_xpath_fail
                    return check_result
                if count > index:
                    result_text = ' '.join(result_node[index].xpath(info_xpath)).strip() if result_node[index].xpath(info_xpath) else ''
                    true_price = deal_price(check_item[id])
                    check_price = deal_price(result_text)
                    if true_price and check_price and float(true_price) == float(check_price):
                        check_result = check_xpath_success
                    else:
                        check_result = check_xpath_wrong
                else:
                    check_result = check_xpath_wrong
            else:
                if count > index:
                    result_text = ' '.join(result_node[index].xpath(info_xpath)).strip() if result_node[index].xpath(info_xpath) else ''
                    check_price = deal_price(result_text)
                    if id in ['price']:
                        true_ori_price = deal_price(check_item['ori_price'])
                        true_cur_price = deal_price(check_item['cur_price'])
                        if check_price and float(check_price) != float(true_ori_price) and float(check_price) != float(true_cur_price):
                            check_result = check_xpath_continue
                    elif id in ['ori_price', 'cur_price']:
                        true_price = deal_price(check_item['price'])
                        if check_price and float(check_price) != float(true_price):
                            check_result = check_xpath_continue
        elif id in ['title', 'brand', 'itemid', 'category', 'skuid']:
            if not check_item.get(id):
                return
            if count == 0:
                check_result = check_xpath_fail
                return check_result
            if count > index:
                result_text = ' '.join(result_node[index].xpath(info_xpath)).strip() if result_node[index].xpath(info_xpath) else ''
                check_text = filter_html_label(result_text)
                if str(check_item[id]).lower() == str(check_text).lower():
                    check_result = check_xpath_success
                else:
                    check_result = check_xpath_wrong
            else:
                check_result = check_xpath_wrong
        elif id in ['img']:
            if not check_item.get(id):
                return
            if count == 0:
                check_result = check_xpath_fail
                return check_result
            if count > index:
                result_text = ' '.join(result_node[index].xpath(info_xpath)).strip() if result_node[index].xpath(info_xpath) else ''
                check_imgs = split_img(result_text)
                check_imgs = [deal_img(i).lower() for i in check_imgs if i]
                true_img = deal_img(check_item[id]).lower()
                if check_imgs and true_img in check_imgs:
                    check_result = check_xpath_success
                else:
                    check_result = check_xpath_wrong
            else:
                check_result = check_xpath_wrong
        elif id in ['img_download']:
            if not check_item.get(id):
                return
            if count == 0:
                check_result = check_xpath_fail
                return check_result
            if count > index:
                check_img = split_img(result_node[index].xpath(info_xpath)[0])[-1] if split_img(result_node[index].xpath(info_xpath)[0]) else ''
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
            else:
                check_result = check_xpath_wrong
        elif id in ['breadlist']:
            if not check_item.get(id):
                return
            if count == 0:
                check_result = check_xpath_fail
                return check_result
            result_text = [filter_html_label(' '.join(node.xpath(info_xpath)).strip().lower()) for node in result_node if node.xpath(info_xpath)]
            true_text = [filter_html_label(text.lower()) for text in check_item[id]]
            if true_text == result_text:
                check_result = check_xpath_success
            else:
                check_result = check_xpath_wrong
        return check_result

    def return_xpath(self, node, key, value, xpath_suffix):
        xpath = None
        if key == None and value == None:
            xpath = "//" + node.tag + xpath_suffix
        if key and key not in key_less:
            num_exist = re.findall(r'\d{5}', value)
            if num_exist or not value or '/@' + key == xpath_suffix or any(field in value for field in value_less):
                xpath = "//" + node.tag + "[@" + key + "]" + xpath_suffix
            else:
                if '"' not in value:
                    xpath = "//" + node.tag + '[@' + key + '="' + value + '"]' + xpath_suffix
                elif "'" not in value:
                    xpath = "//" + node.tag + '[@' + key + "='" + value + "']" + xpath_suffix
        return xpath

    def sort_attrib(self, node, source, target_key=None):
        try:
            #给节点的属性根据匹配数量排序，减少xpath长度
            sort_node_attrib = {}
            key_value_nums = []
            for key, value in node.attrib.items():
                num_exist = re.findall(r'\d{3}', value)
                if key not in key_less and not any(field in value for field in value_less) and not num_exist:
                    if key == target_key:
                        sort_key_value_xpath = f'//{node.tag}[@{key}]'
                    else:
                        if '"' not in value:
                            sort_key_value_xpath = f'//{node.tag}[@{key}="{value}"]'
                        else:
                            sort_key_value_xpath = f"//{node.tag}[@{key}='{value}']"
                    sort_key_value_num = len(source.xpath(sort_key_value_xpath))
                    if sort_key_value_num > 0:
                        key_value_nums.append({
                            'key': key,
                            'num': sort_key_value_num,
                            'value': value
                        })
            key_value_nums = sorted(key_value_nums, key=lambda k: k['num'], reverse=False)
            for key_value_num in key_value_nums:
                sort_node_attrib[key_value_num['key']] = key_value_num['value']
            for key, value in node.attrib.items():
                if key not in sort_node_attrib.keys():
                    sort_node_attrib[key] = value
            return sort_node_attrib
        except:
            return node.attrib

