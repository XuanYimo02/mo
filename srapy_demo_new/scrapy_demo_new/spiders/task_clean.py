import random
import re
import time

import scrapy
import demjson
from scrapy.core.engine import Request

from dmscrapy import defaults
from dmscrapy.task import Task
from dmscrapy.items import BasicItem, PostData
from dmscrapy.dm_spider import DmSpider
from urllib.parse import urljoin, parse_qs, quote, unquote


class DemoSpider(DmSpider):
    name = 'task_clean'
    allowed_domains = ['mk8s.cn', 'baidu.com', '163.com']

    sch_task = 'xhs-works-task'
    sch_batch_size = 10000

    def make_requests_from_url(self, url):
        """
        url 为json格式
        """

        if random.random() < 0.0001:
            return Request(url='https://www.baidu.com', dont_filter=True)

    def parse(self, response, **kwargs):
        pass

