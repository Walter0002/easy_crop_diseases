# -*- coding: utf-8 -*-
import sys
PYTHON_VERSION = int(sys.version.split('.')[0])
import json
import requests
import codecs
import time
import base64
import cv2
import os
import uuid
import threading
import shutil
import time
import numpy as np 
from PIL import Image


url = "http://127.0.0.1:8082/predictor/infer"

output_dir = "test-output"

target_size = [3, 288, 288]  
mean_rgb = [127.5, 127.5, 127.5] 

def crop_image(img, target_size):  
    width, height = img.size  
    w_start = (width - target_size[2]) / 2  
    h_start = (height - target_size[1]) / 2  
    w_end = w_start + target_size[2]  
    h_end = h_start + target_size[1]  
    img = img.crop((w_start, h_start, w_end, h_end))  
    return img  
  
  
def resize_img(img, target_size):  
    ret = img.resize((target_size[1], target_size[2]), Image.BILINEAR)  
    return ret  
  
  
def read_image(img_path):  
    img = Image.open(img_path)  
    if img.mode != 'RGB':  
        img = img.convert('RGB')  
    img = crop_image(img, target_size)  
    img = np.array(img).astype('float32')  
    img -= mean_rgb  
    img = img.transpose((2, 0, 1))  # HWC to CHW  
    img *= 0.007843  
    # print(img.shape)
    img = img[np.newaxis,:]
    # print(img.shape)
    return img  


class TestThread(threading.Thread):
    def __init__(self, thread_id, loop_count):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.loop_count = loop_count

    def run(self):
        with open('test-{}.jpg'.format(self.thread_id), 'rb') as f:
            base64_data = base64.b64encode(f.read())
            if PYTHON_VERSION == 3:
                img_base64 = base64_data.decode()
            else:
                img_base64 = base64_data
        # print(type(img_base64))
        with codecs.open('test-{}.txt'.format(self.thread_id), 'w', encoding='utf-8') as f:
            f.write(img_base64)
        params = {
            'log_id': str(uuid.uuid4().int & (1 << 64) - 1),
            'image': img_base64
        }

        print("thread id:{} start loop".format(self.thread_id))
        for i in range(self.loop_count):
            params['log_id'] = str(uuid.uuid4().int & (1 << 64) - 1)
            time_start = time.time()
            response = requests.post(url, json=params)
            total_cost = (time.time() - time_start) * 1000
            output_flie_name = "thread-" + str(self.thread_id) + '-' + params['log_id'] + ".txt"
            output_flie_name = os.path.join(output_dir, output_flie_name)
            with codecs.open(output_flie_name, 'w', encoding='utf-8') as f:
                f.write('thread id:{} request cost: {}ms\n'.format(self.thread_id, total_cost))
                f.write(response.text)
                result = json.loads(response.text)['data']['result']
                dic = {i:'%.2f'%result[i] for i in range(len(result))}
                sort_dic = sorted(dic.items(), key=lambda d:d[1], reverse = True)
                f.write('\ntop3 label:' + str(sort_dic[:3]) + '\n')
                f.write('predict label:' + str(np.argmax(result)))
        print("thread id:{} loop {} times end".format(self.thread_id, self.loop_count))


if __name__ == '__main__':
    loop_count = 1
    thread_count = 2
    thread_list = []
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    time.sleep(5)
    os.mkdir(output_dir)
    for i in range(thread_count):
        thread = TestThread(i, loop_count)
        thread_list.append(thread)
    start_time = time.time()
    for i in range(len(thread_list)):
        thread_list[i].start()
    for i in range(len(thread_list)):
        thread_list[i].join()
    cost_time = time.time() - start_time
    print("end test, total cost: {}".format(cost_time))
