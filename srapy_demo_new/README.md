# Duomai Scrapy Framework Demo

## How to use it?
step1. install the framework whl

        pip --trusted-host nexus.mk8s.cn install dmscrapy -i http://nexus.mk8s.cn/repository/pypi-group/simple

step2. init scrapy project

        scrapy startproject

step3. config your scrapy project in settings.py
        
        CONTINUOUS_IDLE_AUTO_EXIT = True  # 开启任务获取连续为空退出扩展
        CONTINUOUS_IDLE_NUMBER = 10  # 配置空闲持续时间单位为 360个 ，一个时间单位为5s
        
        # 在 EXTENSIONS 配置，激活扩展
        EXTENSIONS = {
            # 'scrapy_demo.extensions.RedisSpiderSmartIdleClosedExensions': 500,
            'dmscrapy.extensions.DmSpiderSmartIdleClosedExensions': 500
        }
        
        ITEM_PIPELINES = {
            'dmscrapy.pipelines.DmDataDisPipeline2': 100
        }
        
        CONCURRENT_REQUESTS = 1
        DOWNLOAD_DELAY = 1
        
        TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

step4. create your spider extend from DmSpider
        
        from dmscrapy import defaults
        from dmscrapy.task import Task
        from dmscrapy.items import BasicItem, PostData
        from dmscrapy.dm_spider import DmSpider
       
        
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
        
            ...

## If the framework is update, what do you need to do?

step1. upgrade the framework by pip command

        pip --trusted-host nexus.mk8s.cn install --upgrade dmscrapy -i http://nexus.mk8s.cn/repository/pypi-group/simple

or you can uninstall the framework first, and install again

        pip uninstall dmscrapy
        pip --trusted-host nexus.mk8s.cn install dmscrapy -i http://nexus.mk8s.cn/repository/pypi-group/simple

    
## How to build docker image?

step1. add config in pip.conf

        [global]
        index-url=http://nexus.mk8s.cn/repository/pypi-group/simple
        extra-index-url=https://pypi.tuna.tsinghua.edu.cn/simple

        [install]
        trusted-host=pypi.tuna.tsinghua.edu.cn nexus.mk8s.cn

step2. add package in packages.txt
        
        dmscrapy==0.0.3

Attetion: check the lastest version of dm-scrapy-framework, keep the framework newest will be helpful for descrease mistake 
    