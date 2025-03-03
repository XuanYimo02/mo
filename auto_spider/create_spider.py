from spider_tmp.create_tmpl import CreateSpider

if __name__ == "__main__":
    # 【必填】爬虫名称
    spider_name = 'thedoublef'
    # 个人配置
    author = 'Mo'

    s = CreateSpider(spider_name)
    try:
        s.create(
            author=author,
            init_data={
                'spider_name': spider_name,  # 爬虫名 # 必填
            }
        )
    except Exception as e:
        print(e)
