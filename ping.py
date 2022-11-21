import requests
import json
import socket
import time
import os
import yaml
import pynvml

with open(os.path.join(os.path.split(__file__)[0], 'config.yaml')) as f:
    config = yaml.load(f)

pynvml.nvmlInit()
host = config['local']['host']
target = 'http://{}:{}/api/ping'.format(config['lab']['center']['ip'], config['lab']['center']['port'])
target_ip = 'http://{}:{}/api/myip'.format(config['lab']['center']['ip'], config['lab']['center']['port'])
gpu_nums = pynvml.nvmlDeviceGetCount()
handle_list = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(gpu_nums)]


# def get_host_ip():
#     error_count = 0
#     while True:
#         success = False
#         try:
#             res = requests.get(target_ip, '')
#             if res.status_code == 200:
#                 success = True
#                 myip = res.text
#                 return myip
#         except Exception:
#             pass
#         if not success:
#             error_count += 1
#             if error_count > 3:
#                 print('Failed to connect 3 times, try again in 5 minutes...')
#                 time.sleep(5 * 60)
#                 continue
#         else:
#             error_count = 0


def get_host_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip


# def get_gpu_info():
#     gpu_info = {}
#     for i in range(len(handle_list)):
#         meminfo = pynvml.nvmlDeviceGetMemoryInfo(handle_list[i])
#         use = pynvml.nvmlDeviceGetUtilizationRates(handle_list[i])
#         brand = pynvml.nvmlDeviceGetName(handle_list[i]).decode("utf-8")
#         #original
#         #gpu_info[i] = {
#         #    'status': '{:.1f}M/{:.1f}M'.format(meminfo.used / 2**20, meminfo.total / 2**20),
#         #    'percentage': round(meminfo.used / meminfo.total * 100)
#         #}
#         gpu_info[i] = {
#             'status': '{:.1f}M/{:.1f}M'.format(meminfo.used / 2**20, meminfo.total / 2**20),
#             'percentage': round(use.gpu),
#             'brand' : brand
#         }
#     return gpu_info

def get_gpu_info():

    from gpustat import GPUStatCollection
    try:
        stat = GPUStatCollection.new_query().jsonify()
        delete_list = []
        for gpu_id, gpu in enumerate(stat['gpus']):
            if type(gpu['processes']) is str:
                delete_list.append(gpu_id)
                continue
            gpu['memory'] = round(float(gpu['memory.used']) /
                                  float(gpu['memory.total']) * 100)
            
            gpu['users'] = len(set([p['username']
                                    for p in gpu['processes']]))
            user_process = [
                '%s(%s,%sM)' % (p['username'],
                                p['command'], p['gpu_memory_usage'])
                for p in gpu['processes']
            ]
            gpu['user_processes'] = ' '.join(user_process)

            gpu['flag'] = 'bg-primary'
            if gpu['temperature.gpu'] > 75:
                gpu['flag'] = 'bg-danger'
            elif gpu['temperature.gpu'] > 50:
                gpu['flag'] = 'bg-warning'
            elif gpu['temperature.gpu'] > 25:
                gpu['flag'] = 'bg-success'

        if delete_list:
            for gpu_id in delete_list:
                stat['gpus'].pop(gpu_id)

        return stat
    except Exception as e:
        return {'error': '%s!' % getattr(e, 'message', str(e))}


if __name__ == "__main__":
    body = {
        'ip': None,  
        'gpu_nums': gpu_nums,
        'gpu_info': {}, 
        '_date': None}
    error_count = 0
    while True:
        body['ip'] = get_host_ip()
        body['gpu_info'] = get_gpu_info()
        body['_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        success = False
        try:
            res = requests.post(target, json.dumps(body,default=str))
            if res.status_code == 200:
                success = True
                print('Success ping')
        except Exception:
            pass
        if not success:
            error_count += 1
            if error_count > 3:
                print('Failed to connect 3 times, try again in 5 minutes...')
                time.sleep(5 * 60)
                continue
        else:
            error_count = 0
        time.sleep(30)