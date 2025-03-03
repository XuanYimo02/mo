# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import base64
import logging
import json
import random
import time
import cloudscraper
import httpx
import requests
import sys
from curl_cffi import requests as curl_requests
from tls_client import Session
from scrapy import signals
from scrapy.http import HtmlResponse
from urllib.parse import urldefrag
from twisted.internet import threads
from twisted.internet.error import TimeoutError
from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from oversea_mall.spiders.utils.redis_tools import RedisServer
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from oversea_mall.settings import PROXY_MAP, PROXY_SERVER, DM_DIS_URL, VPS_PROXY, REDIS_HOST, REDIS_PORT, REDIS_PWD, \
    OVERSEA_PROXY, OVERSEA_DMPROXY
from curl_cffi.requests.errors import RequestsError as curl_cffi_RequestsError
from curl_cffi.curl import CurlError
from fake_headers import Headers

logger = logging.getLogger(__name__)

class OverseaProxyMiddleware:
    def process_request(self, request, spider):
        proxy_string = None
        if DM_DIS_URL not in request.url:
            if sys.platform == 'win32':
                proxy_string = 'http://127.0.0.1:7890'

            if sys.platform == 'darwin':
                proxy_string = 'http://127.0.0.1:7890'

            if sys.platform == 'linux':
                proxy_string = OVERSEA_PROXY

            if proxy_string:
                request.meta['proxy'] = proxy_string
                request.meta['full_proxy'] = proxy_string


class OverseaDMProxyMiddleware:
    def process_request(self, request, spider):
        proxy_string = None
        if DM_DIS_URL not in request.url:
            if sys.platform == 'win32':
                proxy_string = 'http://127.0.0.1:7890'

            if sys.platform == 'darwin':
                proxy_string = 'http://127.0.0.1:7890'

            if sys.platform == 'linux':
                proxy_string = OVERSEA_DMPROXY

            if proxy_string:
                request.meta['proxy'] = proxy_string
                request.meta['full_proxy'] = proxy_string


class RequestsMiddleWare(object):
    """
    有时scrapy请求总是有问题，可以试试换成 requests 请求 + 代理
    """
    def __init__(self, **kwargs):
        self.encoding = kwargs.get('ENCODING', 'utf-8')
        self.time_out = kwargs.get('DOWNLOAD_TIMEOUT', 60)
        self.delay = kwargs.get('DOWNLOAD_DELAY', 0)

    def process_request(self, request, spider):
        headers = {key.decode('utf-8'): value[0].decode('utf-8') for key, value in request.headers.items()}
        proxy_string = request.meta.get('proxy')
        if proxy_string:
            current_proxies = {
                'http': proxy_string,
                'https': proxy_string,
            }
        else:
            current_proxies = {}

        _cookies = request.cookies
        if request.meta.get('payload'):
            response = requests.post(url=request.url, data=json.dumps(request.meta.get('payload')), headers=headers, cookies=_cookies,
                                     timeout=self.time_out, proxies=current_proxies, allow_redirects=False)
        elif request.method == 'POST':
            req_params = dict(url=request.url, data=request.body, headers=headers, cookies=_cookies,
                              timeout=self.time_out, proxies=current_proxies, allow_redirects=False)
            response = requests.post(**req_params)
            del req_params
        else:
            response = requests.get(url=request.url, headers=headers, cookies=_cookies,
                                    timeout=self.time_out, proxies=current_proxies, allow_redirects=False)
        if self.delay > 0:
            time.sleep(self.delay)
        request.meta['dont_redirect'] = True
        return HtmlResponse(url=request.url, headers=response.headers,
                            body=response.content, request=request, encoding=self.encoding,
                            status=response.status_code)


class RequestsDownloadHandler(HTTP11DownloadHandler):

    def __init__(self, settings, crawler=None):
        super().__init__(settings, crawler)
        self.setting = crawler.settings
        self.encoding = self.setting.get('ENCODING', 'utf-8')
        self.time_out = self.setting.get('DOWNLOAD_TIMEOUT', 60)
        self.delay = self.setting.get('DOWNLOAD_DELAY', 0)
        self.allow_redirects = self.setting.get('REDIRECT_ENABLED', True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler)

    def download_request(self, request, spider):
        from twisted.internet import reactor
        timeout = self.time_out
        # request details
        url = urldefrag(request.url)[0]
        start_time = time.time()

        # Embedding the provided code asynchronously
        d = threads.deferToThread(self._async_download, request)

        # set download latency
        d.addCallback(self._cb_latency, request, start_time)
        # check download timeout
        # self._timeout_cl = reactor.callLater(timeout, d.cancel)
        # d.addBoth(self._cb_timeout, url, timeout)
        return d

    def _async_download(self, request):
        headers = {key.decode('utf-8'): value[0].decode('utf-8') for key, value in request.headers.items()}
        proxy_string = request.meta.get('full_proxy')
        if proxy_string:
            current_proxies = {
                'http': proxy_string,
                'https': proxy_string,
            }
        else:
            current_proxies = {}

        _cookies = request.cookies
        if request.method == 'POST':
            response = requests.post(url=request.url, data=request.body, headers=headers, cookies=_cookies,
                              timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects)
        else:
            response = requests.get(url=request.url, headers=headers, cookies=_cookies,
                                    timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects)
        if self.delay > 0:
            time.sleep(self.delay)
        request.meta['dont_redirect'] = True
        return HtmlResponse(url=request.url, headers=response.headers,
                            body=response.content, request=request, encoding=self.encoding,
                            status=response.status_code)

    # def _cb_timeout(self, result, url, timeout):
    #     if self._timeout_cl.active():
    #         self._timeout_cl.cancel()
    #         return result
    #     raise TimeoutError(f"Getting {url} took longer than {timeout} seconds.")

    def _cb_latency(self, result, request, start_time):
        request.meta["download_latency"] = time.time() - start_time
        return result


class CloudscraperDownloadHandler(HTTP11DownloadHandler):

    def __init__(self, settings, crawler=None):
        super().__init__(settings, crawler)
        self.setting = crawler.settings
        self.encoding = self.setting.get('ENCODING', 'utf-8')
        self.time_out = self.setting.get('DOWNLOAD_TIMEOUT', 60)
        self.delay = self.setting.get('DOWNLOAD_DELAY', 0)
        self.allow_redirects = self.setting.get('REDIRECT_ENABLED', True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler)

    def download_request(self, request, spider):
        from twisted.internet import reactor
        timeout = self.time_out
        # request details
        url = urldefrag(request.url)[0]
        start_time = time.time()

        # Embedding the provided code asynchronously
        d = threads.deferToThread(self._async_download, request)

        # set download latency
        d.addCallback(self._cb_latency, request, start_time)
        # check download timeout
        # self._timeout_cl = reactor.callLater(timeout, d.cancel)
        # d.addBoth(self._cb_timeout, url, timeout)
        return d

    def _async_download(self, request):
        scraper = cloudscraper.create_scraper()
        headers = {key.decode('utf-8'): value[0].decode('utf-8') for key, value in request.headers.items()}
        proxy_string = request.meta.get('full_proxy')
        if proxy_string:
            current_proxies = {
                'http': proxy_string,
                'https': proxy_string,
            }
        else:
            current_proxies =  {}

        _cookies = request.cookies
        if request.method == 'POST':
            response = scraper.post(url=request.url, data=request.body, headers=headers, cookies=_cookies,
                              timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects)
        else:
            response = scraper.get(url=request.url, headers=headers, cookies=_cookies,
                                    timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects)
        if self.delay > 0:
            time.sleep(self.delay)
        request.meta['dont_redirect'] = True
        return HtmlResponse(url=request.url, headers=response.headers,
                            body=response.content, request=request, encoding=self.encoding,
                            status=response.status_code)

    # def _cb_timeout(self, result, url, timeout):
    #     if self._timeout_cl.active():
    #         self._timeout_cl.cancel()
    #         return result
    #     raise TimeoutError(f"Getting {url} took longer than {timeout} seconds.")

    def _cb_latency(self, result, request, start_time):
        request.meta["download_latency"] = time.time() - start_time
        return result


class CurlDownloadHandler(HTTP11DownloadHandler):

    def __init__(self, settings, crawler=None):
        super().__init__(settings, crawler)
        self.setting = crawler.settings
        self.encoding = self.setting.get('ENCODING', 'utf-8')
        self.time_out = self.setting.get('DOWNLOAD_TIMEOUT', 60)
        self.delay = self.setting.get('DOWNLOAD_DELAY', 0)
        self.allow_redirects = self.setting.get('REDIRECT_ENABLED', True)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler)

    def download_request(self, request, spider):
        from twisted.internet import reactor
        timeout = self.time_out
        # request details
        url = urldefrag(request.url)[0]
        start_time = time.time()

        # Embedding the provided code asynchronously
        d = threads.deferToThread(self._async_download, request)

        # set download latency
        d.addCallback(self._cb_latency, request, start_time)
        # check download timeout
        # self._timeout_cl = reactor.callLater(timeout, d.cancel)
        # d.addBoth(self._cb_timeout, url, timeout)
        return d

    def _async_download(self, request):
        headers = {key.decode('utf-8'): value[0].decode('utf-8') for key, value in request.headers.items()}
        proxy_string = request.meta.get('full_proxy')
        if proxy_string:
            current_proxies = {
                'http': proxy_string,
                'https': proxy_string,
            }
        else:
            current_proxies =  {}

        _cookies = request.cookies
        if request.method == 'POST':
            response = curl_requests.post(url=request.url, data=request.body, headers=headers, cookies=_cookies,
                              timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects, impersonate='chrome110')
        else:
            response = curl_requests.get(url=request.url, headers=headers, cookies=_cookies,
                                    timeout=self.time_out, proxies=current_proxies, allow_redirects=self.allow_redirects, impersonate='chrome110')
        if self.delay > 0:
            time.sleep(self.delay)
        request.meta['dont_redirect'] = True
        return HtmlResponse(url=request.url, headers=response.headers,
                            body=response.content, request=request, encoding=self.encoding,
                            status=response.status_code)

    # def _cb_timeout(self, result, url, timeout):
    #     if self._timeout_cl.active():
    #         self._timeout_cl.cancel()
    #         return result
    #     raise TimeoutError(f"Getting {url} took longer than {timeout} seconds.")

    def _cb_latency(self, result, request, start_time):
        request.meta["download_latency"] = time.time() - start_time
        return result


class CurlRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        super().__init__(settings)
        ERROR_TYPE = settings.get('ERROR_TYPE', ())
        if not hasattr(self, 'exceptions_to_retry'):
            self.exceptions_to_retry = self.EXCEPTIONS_TO_RETRY
        self.exceptions_to_retry = self.exceptions_to_retry + (CurlError,curl_cffi_RequestsError) + ERROR_TYPE
        self.EXCEPTIONS_TO_RETRY = self.EXCEPTIONS_TO_RETRY + (CurlError,curl_cffi_RequestsError) + ERROR_TYPE


class OverseaHTTP2Middleware:
    async def process_request(self, request, spider):
        headers = request.headers.to_unicode_dict()
        headers['User-Agent'] = Headers(os="win").generate()['User-Agent']
        if DM_DIS_URL not in request.url:
            try:
                async with httpx.AsyncClient(http2=True, headers=headers, proxies=OVERSEA_DMPROXY) as client:
                    if request.method == "GET":
                        response = await client.get(request.url)
                    else:
                        response = await client.post(request.url)
                    return HtmlResponse(
                        url=request.url,
                        status=response.status_code,
                        body=response.content,
                        encoding="utf-8",
                        request=request,
                        # meta=self.request.meta,
                    )
            except:
                return request