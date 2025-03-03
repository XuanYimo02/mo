import os
import sys
from datetime import datetime

if __name__ == "__main__":
    delet_logs = []
    spider_logs = {}
    today = datetime.now()
    logs_path = './oversea_mall/spider_logs'
    logs_list = os.listdir(logs_path)
    sort_logs_dict = {}
    for log in logs_list:
        log_name = log.split('.log')[0]
        try:
            log_year = log_name.split('_')[-3]
            log_month = log_name.split('_')[-2]
            if int(log_month) < 10:
                log_month = '0' + log_month
            log_day = log_name.split('_')[-1]
            if int(log_day) < 10:
                log_day = '0' + log_day
            sort_logs_dict[log] = int(log_year+log_month+log_day)
        except:
            sort_logs_dict[log] = 0
    sort_logs_dict = sorted(sort_logs_dict.items(), key=lambda x: x[1])
    for log_name in sort_logs_dict:
        log_name = log_name[0]
        if '_' in log_name:
            spider_name = '_'.join(log_name.split('_')[0:-3])
            if spider_name in spider_logs.keys():
                spider_logs[spider_name].append(log_name)
            else:
                spider_logs[spider_name] = []
                spider_logs[spider_name].append(log_name)
    for key,value in spider_logs.items():
        if len(value) > 3:
            delet_spider_logs = value[0:-3]
            for delet_spider_log in delet_spider_logs:
                delet_logs.append(delet_spider_log)
    print(delet_logs)
    for delet_log in delet_logs:
        try:
            delet_log_path = f'./oversea_mall/spider_logs/{delet_log}'
            os.remove(delet_log_path)
        except Exception as e:
            print(f'DELET {delet_log} WRONG，ERROR: {e}')