# Scrapy settings for oversea_mall project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'oversea_mall'

SPIDER_MODULES = ['oversea_mall.spiders']
NEWSPIDER_MODULE = 'oversea_mall.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'oversea_mall (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'oversea_mall.middlewares.OverseaMallSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'oversea_mall.middlewares.OverseaMallDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'oversea_mall.pipelines.OverseaMallPipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'



CONTINUOUS_IDLE_AUTO_EXIT = True  # 开启任务获取连续为空退出扩展
CONTINUOUS_IDLE_NUMBER = 120  # 配置空闲持续时间单位为 360个 ，一个时间单位为5s

# 在 EXTENSIONS 配置，激活扩展
EXTENSIONS = {
    # 'scrapy_demo.extensions.RedisSpiderSmartIdleClosedExensions': 500,
    'dmscrapy.extensions.DmSpiderSmartIdleClosedExensions': 500
}

ITEM_PIPELINES = {
    'dmscrapy.pipelines.DmDataDisPipeline2': 100
}

CONCURRENT_REQUESTS = 100
DOWNLOAD_DELAY = 0

# scrapy.utils.reactor.install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
#
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
# 隧道代理配置
PROXY_SERVER = "http://http-dyn.abuyun.com:9020"
PROXY_MAP = {
    # "ali": {"user": "HA48HGSB02F4TCSD", "pass": "691FEB759FF01369"},
    "weibo": {"user": "HAZ8395D9E0I92DD", "pass": "F087B0CEFCAB6B0A"},
    "bilibili": {"user": "H85CQ988836IT4HD", "pass": "F3808744647EF726"},
    'nike': {"user": "HK4W21A90YWE68MD", "pass": "4AF254577248760B"},
}


# HTTPERROR_ALLOWED_CODES = [302,412,-412,400,410,404,429,403,500]
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 400, 403, 405, 429]
HTTPERROR_ALLOWED_CODES = [400]

# 任务调度
# 本地
DM_SCHEDULER_URL = 'https://dm-magellan-crawler-task.mktdatatech.com/task/'  # 任务调度服务地址

# 本地联调
# DM_SCHEDULER_URL = 'http://172.16.7.59:8094/task/'

# 线上
# DM_SCHEDULER_URL = 'http://dm-crawler-task.spider-server.svc.cluster.local:8084/task/'  # 任务调度服务地址

DM_SCHEDULER_PULL_API = 'pullTask'  # 拉取任务API
DM_SCHEDULER_ADD_API = 'addTask'  # 添加同类型多条任务API
DM_SCHEDULER_HAS_API = 'existTask'  # 判断是否还有任务
DM_SCHEDULER_MULTI_ADD_API = 'addMultiTask'  # 添加多个不同类型多个任务
DM_SCHEDULER_CALLBACK_API = 'taskCallback'  # 任务回调API
DM_SCHEDULER_API_SUCCESS_CODE = 0  # 成功标识
DM_SCHEDULER_TASK_ID = '_taskId'  # 任务ID
DM_SCHEDULER_FORCE_TASK = '_forceTask'  # 是否需要进行回调

# 数据接入
# 本地
DM_DIS_URL = 'https://magellan-dis.mktdatatech.com/post/submit'  # 数据上报地址

# 线上
# DM_DIS_URL = 'http://dm-dis.dataplus.svc.cluster.local:8081/post/submit'  # 数据上报地址


# 本地联调
# url =  "http://172.16.7.103:8094/task/taskCallback"
# DM_DIS_URL = 'http://172.16.7.59:8094/post/submit'

# 拉取更新任务api
# item_update_api = 'http://dm-erec-admin.erec-server.svc.cluster.local:20880/api/item/scroll' #线上
item_update_api = 'https://dm-erec-admin-erec-server.mktdatatech.com/api/item/scroll'


# redis
REDIS_HOST = '115.238.100.72'
REDIS_PORT = 31685
REDIS_DB = 5
REDIS_PWD = ''

# COOKIES_ENABLED = False
VPS_PROXY = 'https://vps-proxy.mk8s.cn/'


DM_SCHEDULER_URL = 'http://dm-magellan-crawler-task.mktdatatech.com/task/'
# 任务调度服务地址
DM_DIS_URL = 'http://magellan-dis.mktdatatech.com/post/submit'

#海外代理
# OVERSEA_PROXY = 'http://astoip451:ef1772-d18d43-e0da31-41f501-ed5f24@209.205.212.35:9001'
OVERSEA_PROXY = 'http://astoip451-country-US:ef1772-d18d43-e0da31-41f501-ed5f24@209.205.219.18:9001'
OVERSEA_DMPROXY = 'http://user-shop898-region-us:duomai898@pr-na.roxlabs.cn:4600'
# OVERSEA_DMPROXY = 'http://user-dm_jokerj-region-us:dm_123456@pr-na.roxlabs.cn:4600'

COMPRESSION_ENABLED = False