import multiprocessing
import os
import time
from scrapy import cmdline
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import subprocess
today = datetime.now()

def run_scrapy_crawl(command):
    p = subprocess.Popen(f'ps aux |grep "{command}" | grep -v grep', stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                         shell=True)
    stdout, stderr = p.communicate()
    process_number = stdout.decode('gbk') + stderr.decode('gbk')
    if process_number:
        print(f'{command} 已经在运行')
    else:
        print(f'{today.year} {today.month} {today.day} {today.time()} run command {command} start')
        os.system(command)
        print(f'{today.year} {today.month} {today.day} {today.time()} run command {command} done')

if __name__ == '__main__':

    #每天运行一次
    commands = [
        'python3 ./oversea_mall/spiders/32degrees.py',
        'python3 ./oversea_mall/spiders/alexanderwang.py',
        'python3 ./oversea_mall/spiders/allbirds.py',
        'python3 ./oversea_mall/spiders/alumniofny.py',
        'python3 ./oversea_mall/spiders/arcteryx.py',
        'python3 ./oversea_mall/spiders/balardi.py',
        'python3 ./oversea_mall/spiders/balmain.py',
        'python3 ./oversea_mall/spiders/baracuta.py',
        'python3 ./oversea_mall/spiders/bergdorfgoodman.py',
        'python3 ./oversea_mall/spiders/beyondyoga.py',
        'python3 ./oversea_mall/spiders/bluebella.py',
        'python3 ./oversea_mall/spiders/bootbarn.py',
        'python3 ./oversea_mall/spiders/brandonblackwood.py',
        'python3 ./oversea_mall/spiders/cabbagesandroses.py',
        'python3 ./oversea_mall/spiders/citizenwatch.py',
        'python3 ./oversea_mall/spiders/clarks.py',
        'python3 ./oversea_mall/spiders/corridornyc.py',
        'python3 ./oversea_mall/spiders/countryattire.py',
        'python3 ./oversea_mall/spiders/couverture.py',
        'python3 ./oversea_mall/spiders/cupshe.py',
        'python3 ./oversea_mall/spiders/cuyana.py',
        'python3 ./oversea_mall/spiders/diesel.py',
        'python3 ./oversea_mall/spiders/droledemonsieur.py',
        'python3 ./oversea_mall/spiders/eberjey.py',
        'python3 ./oversea_mall/spiders/freepeople.py',
        'python3 ./oversea_mall/spiders/gucci.py',
        'python3 ./oversea_mall/spiders/hanaleicompany.py',
        'python3 ./oversea_mall/spiders/hauteflair.py',
        'python3 ./oversea_mall/spiders/heist-studios.py',
        'python3 ./oversea_mall/spiders/hourglasscosmetics.py',
        'python3 ./oversea_mall/spiders/italist.py',
        'python3 ./oversea_mall/spiders/koio.py',
        'python3 ./oversea_mall/spiders/lacoste.py',
        'python3 ./oversea_mall/spiders/landsend.py',
        'python3 ./oversea_mall/spiders/lonedesignclub.py',
        'python3 ./oversea_mall/spiders/maceoo.py',
        'python3 ./oversea_mall/spiders/mansurgavriel.py',
        'python3 ./oversea_mall/spiders/minnetonkamoccasin.py',
        'python3 ./oversea_mall/spiders/nanushka.py',
        'python3 ./oversea_mall/spiders/olivela.py',
        'python3 ./oversea_mall/spiders/pacsun.py',
        'python3 ./oversea_mall/spiders/patagonia.py',
        'python3 ./oversea_mall/spiders/patmcgrath.py',
        'python3 ./oversea_mall/spiders/petitestudionyc.py',
        'python3 ./oversea_mall/spiders/pianoluigi.py',
        'python3 ./oversea_mall/spiders/proozy.py',
        'python3 ./oversea_mall/spiders/rogervivier.py',
        'python3 ./oversea_mall/spiders/strathberry.py',
        'python3 ./oversea_mall/spiders/stuartweitzman.py',
        'python3 ./oversea_mall/spiders/stussy.py',
        'python3 ./oversea_mall/spiders/sunnei.py',
        'python3 ./oversea_mall/spiders/themessistore.py',
        'python3 ./oversea_mall/spiders/vans.py',
        'python3 ./oversea_mall/spiders/venum.py',
        'python3 ./oversea_mall/spiders/verabradley.py',
        'python3 ./oversea_mall/spiders/victoriabeckham.py',
        'python3 ./oversea_mall/spiders/wolven.py',
        'python3 ./oversea_mall/spiders/ysl.py',
        'python3 ./oversea_mall/spiders/yummie.py',
        'python3 ./oversea_mall/spiders/stradivarius.py',
        'python3 ./oversea_mall/spiders/arket.py',
        'python3 ./oversea_mall/spiders/louxly.py',
        'python3 ./oversea_mall/spiders/miinto.py',
    ]
    executor = ThreadPoolExecutor(max_workers=6)
    for data in executor.map(run_scrapy_crawl, commands):
        pass

    # with multiprocessing.Pool(processes=6) as pool:
    #     # 使用进程池执行所有命令
    #     pool.map(run_scrapy_crawl, commands)
    # print(f'{today.year} {today.month} {today.day} run command over')