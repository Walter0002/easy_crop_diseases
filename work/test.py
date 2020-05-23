# -*- coding: utf-8 -*-
import sys
PYTHON_VERSION = int(sys.version.split('.')[0])
import json
import requests
import codecs
import time
import base64
import os
import uuid
import threading
import shutil
import time
import numpy as np 


def main(id):
    with open('test-1.jpg'.format(id), 'rb') as f:
        base64_data = base64.b64encode(f.read())
        if PYTHON_VERSION == 3:
            img_base64 = base64_data.decode()
        else:
            img_base64 = base64_data
    # print(type(img_base64))
    with codecs.open('test-{}.txt'.format(id), 'w', encoding='utf-8') as f:
        f.write(img_base64)
    params = {
        'log_id': str(uuid.uuid4().int & (1 << 64) - 1),
        'image': img_base64
    }

    print("img id:{} start loop".format(id))
    time_start = time.time()
    response = requests.post(url, json=params)
    total_cost = (time.time() - time_start) * 1000
    output_flie_name = "thread-" + str(id) + '-' + params['log_id'] + ".txt"
    output_flie_name = os.path.join(output_dir, output_flie_name)
    with codecs.open(output_flie_name, 'w', encoding='utf-8') as f:
        f.write('img id:{} request cost: {}ms\n'.format(id, total_cost))
        f.write(response.text)
        result = json.loads(response.text)['data']['result']
        dic = {i:'%.2f'%result[i] for i in range(len(result))}
        sort_dic = sorted(dic.items(), key=lambda d:d[1], reverse = True)
        f.write('\ntop3 label:' + str(sort_dic[:3]) + '\n')
        f.write('predict label:' + str(np.argmax(result)))
    print("img id:{} loop {} times end".format(id, 1))


if __name__ == '__main__':
    url = "http://localhost:8082/predictor/infer"
    output_dir = "test-output"
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    time.sleep(5)
    os.mkdir(output_dir)
    
    start_time = time.time()
    main(1)
    cost_time = time.time() - start_time
    print("end test, total cost: {}".format(cost_time))
