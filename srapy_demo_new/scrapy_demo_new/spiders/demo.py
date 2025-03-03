import json
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
    name = 'dm_demo'
    allowed_domains = ['mk8s.cn', 'baidu.com', '163.com']

    sch_task = 'test-task'
    sch_batch_size = 10000

    def make_requests_from_url(self, url):
        """
        url 为json格式
        """

        print(url)
        return Request(url='https://www.baidu.com', dont_filter=True)

    def parse(self, response, **kwargs):
        print(
            f'{response.url}\t {response.meta.get(defaults.DM_SCHEDULER_TASK_ID)}\t {response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)}')

        resp = demjson.decode(response.body.decode(response.encoding))

        # 对于强制成功类型(forceTask=true and taskId is not None)的任务，可以结合实际情况手动触发任务状态回调
        # 如根据response中数据返回的状态码（非http状态码），判断响应数据是否正常。失败则手动触发失败回调接口 （这种类型框架层面无法处理，因为不会走pipeline）
        # 重要：成功（success_callback）类型建议不要手动触发，而应该交给框架处理（在pipeline中，当数据提交成功后才执行成功回调，因为解析过程可能会报错，提交数据也可能失败）
        # 其他情形，可以让平台自行处理（任务有超时机制，timeout时间范围内如果未收到任何任务状态回调，平台会自动重放该任务（重试次数范围内））
        if response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK) and response.meta.get(
                defaults.DM_SCHEDULER_TASK_ID) and resp.get('status', 'error') != 'success':
            self.failed_callback(response.meta.get(defaults.DM_SCHEDULER_TASK_ID))

        # 通过构造函数初始化
        task = Task({"taskName": "test", "submitter": "test-spider", "taskData": ["test"]})

        # 空构造函数后赋值
        task = Task()
        task.taskName = 'test'
        task.submitter = 'test-submitter'
        task.forceTask = True  # False
        task.timeout = 10
        task.weight = 100
        task.taskData = [{"platform": "xhs", "source_id": "6666666", "updatedFocus": True},
                         {"platform": "xhs", "source_id": "6666666", "updateFocus": False}]

        # 同类型任务提交多个任务
        self.push_task(task)

        # 不同类型任务提交多个任务
        task1 = Task()
        task1.taskName = 'xhs-works-task'
        task1.submitter = 'test1-submitter'
        task1.globalFilter = True  # False
        # task1.timeout = 10
        # task1.weight = 100
        task1.taskData = [{"sourceId": "6666666", "updateComment": 1},
                          {"sourceId": "6666666", "updateComment": 1}]
        self.push_tasks([task, task1])

        yield Request(url='https://www.163.com', callback=self.parse_step2, meta=response.meta, dont_filter=True)

    def parse_step2(self, response):
        print(
            f'{response.url}\t {response.meta.get(defaults.DM_SCHEDULER_TASK_ID)}\t {response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)}')
        item = {
            'fetch_time': time.time(),
            'nick': 'nnnnnn'
        }
        data = PostData()
        data['dataRows'] = [item, item]
        data['name'] = 'test'
        data[defaults.DM_SCHEDULER_TASK_ID] = response.meta.get(defaults.DM_SCHEDULER_TASK_ID)
        data[defaults.DM_SCHEDULER_FORCE_TASK] = response.meta.get(defaults.DM_SCHEDULER_FORCE_TASK)
        yield data
