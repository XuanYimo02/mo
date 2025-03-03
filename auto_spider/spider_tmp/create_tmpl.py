import os
import time
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))))
base_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class CreateSpider(object):
    def __init__(self, spider_name):
        self.spider_name = spider_name
        self.spider_path = rf'{base_path}//oversea_mall//spiders//{self.spider_name}.py'

    def _replace_file_info(self, file, **kwargs):
        """
        It replaces the placeholders in the template file with the values passed in the kwargs

        :param file: the file content to be replaced
        :return: The file is being returned.
        """

        author = kwargs.get('author', '')
        created_at = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        file = file.replace("${time}", created_at)
        file = file.replace("${author}", author)
        file = file.replace("${spider_name}", self.spider_name)

        return file

    def _get_spider_template(self):
        """
        It opens a file, reads it, and returns the contents of the file
        :return: The spider_template is being returned.
        """
        template_path = rf'{base_path}//spider_tmp//spider_template.tmpl'
        with open(template_path, "r", encoding="utf-8") as file:
            spider_template = file.read()
        return spider_template

    def _save_template_to_file(self, tmpl_file):
        """
        It takes a template file and a target path, and writes the template file to the target path

        :param tmpl_file: The template file that you want to save to a file
        :param target_path: The path to the file you want to save the template to
        """
        with open(self.spider_path, "w", encoding="utf-8") as file:
            file.write(tmpl_file)

    def _create_spider(self, **kwargs):
        """
        It takes a template file, replaces the placeholders with the values passed in the kwargs, and
        saves the file to the target path
        """
        tmpl = self._get_spider_template()
        tmpl_file = self._replace_file_info(tmpl, **kwargs)
        self._save_template_to_file(tmpl_file)

    def create(self, **kwargs):
        """
        It creates a spider.
        """
        init_data = kwargs.get('init_data')
        if not self.spider_name:
            raise NameError("spidername不允许为空, 请检查！")
        if os.path.exists(self.spider_path):
            raise NameError(f"爬虫{self.spider_name}已存在, 请检查！")
        self._create_spider(**kwargs)
        msg = f"爬虫{self.spider_name}创建成功"
        print(msg)

