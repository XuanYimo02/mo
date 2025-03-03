# -*- coding: utf-8 -*-
import logging
from typing import Optional

import requests
from requests import request
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception
from user_agent import generate_user_agent


class RequestStatusError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


VALID_STATUS_CODES = [200, 302]

RETRY_EXCEPTIONS = [
    requests.exceptions.ProxyError,
    requests.exceptions.ReadTimeout,
    requests.exceptions.ChunkedEncodingError,
    ConnectionResetError,
    RequestStatusError
]


class RetryIfExceptionTypes(retry_if_exception):
    def __init__(self, exception_types: Optional[list] = None):
        self.exception_types = exception_types if exception_types else [Exception]
        super(RetryIfExceptionTypes, self).__init__(self.catch_exceptions)

    def catch_exceptions(self, e):
        for exception in self.exception_types:
            if isinstance(e, exception):
                return True


def httpx_error_callback(retry_state):
    logging.error(f'request 异常 {retry_state.args} {retry_state.kwargs}')
    return None


retry_if_exception_types = RetryIfExceptionTypes


class BaseSpider(object):
    default_headers = {
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application"
            "/signed-exchange;v=b3;q=0.9"),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en;q=0.7",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
            "/79.0.3945.130 Safari/537.36"),
    }

    @staticmethod
    @retry(
        wait=wait_fixed(2),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_types(RETRY_EXCEPTIONS),
        retry_error_callback=httpx_error_callback,
    )
    def fetch(url, method='get', randua=False, **kwargs):
        """
        处理具体请求
        :param method:
        :param url:
        :param randua:
        :param kwargs:
        :return:
        """
        if method == 'get':
            kwargs.setdefault('allow_redirects', True)
        if not kwargs.get('timeout'):
            kwargs.setdefault('timeout', 2)
        if not kwargs.get('headers'):
            kwargs.setdefault('headers', BaseSpider.default_headers)
        if randua:
            kwargs['headers']['user-agent'] = generate_user_agent()

        response = request(method=method, url=url, **kwargs)
        if response.status_code in VALID_STATUS_CODES:
            return response
        else:
            raise RequestStatusError

    @staticmethod
    def aby_proxy(meta=False):
        proxy_host = "http-dyn.abuyun.com"
        proxy_port = "9020"

        # 代理隧道验证信息
        proxy_user = "HAZ8395D9E0I92DD"
        proxy_pass = "F087B0CEFCAB6B0A"

        proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxy_host,
            "port": proxy_port,
            "user": proxy_user,
            "pass": proxy_pass,
        }
        if meta:
            return proxy_meta

        proxies = {
            "http": proxy_meta,
            "https": proxy_meta,
        }
        return proxies


fetch = BaseSpider.fetch
