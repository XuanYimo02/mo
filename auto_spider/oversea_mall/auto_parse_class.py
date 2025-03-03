from functools import wraps
import logging
from auto_parse.tools import get_old_parse_info

logger = logging.getLogger(__name__)

class AutoParse(object):

    xpath_list = {}
    json_list = {}
    check_old_parse_info_flag = False
    auto_parse_info_path = None

    def check_parse_info(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.check_old_parse_info_flag == False and self.xpath_list == {} and self.json_list == {}:
                logger.info('加载旧解析数据')
                self.check_old_parse_info_flag = True
                self.xpath_list, self.json_list = get_old_parse_info(self.auto_parse_info_path)
            return func(self, *args, **kwargs)
        return wrapper