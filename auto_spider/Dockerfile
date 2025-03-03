# Version 0.1

# 基础镜像
FROM harbor.duomai.com/spider/server/scrapy-python:3.6-alpine

# 切换工作目录
WORKDIR /usr/local/share/oversea_mall

# 拷贝文件
COPY pip.conf /root/.pip/pip.conf
COPY . /usr/local/share/oversea_mall/


COPY . /tekton/home/

# 执行包的安装
RUN cd /usr/local/share/oversea_mall && pip3 install --upgrade pip && pip3 install -r packages.txt

# 启动镜像的时候执行命令
ENTRYPOINT ["/bin/bash","/usr/local/share/oversea_mall/scrapy-run.sh"]
#ENTRYPOINT ["/bin/bash","/tekton/home/scrapy-run.sh"]
