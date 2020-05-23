# -*- coding: utf-8 -*-
"""
数据处理的方式写在这里
"""
import cv2
import numpy as np
import base64
import time
import sys
from PIL import Image
from conf.server_conf import config
from utils.logger_util import logger
from paddle.fluid.core import PaddleBuf
from paddle.fluid.core import PaddleDType
from paddle.fluid.core import PaddleTensor
PYTHON_VERSION = int(sys.version.split('.')[0])


def warp_input(image_data, input_size):
    """
    deal input to paddle tensor
    :param image_data:          输入的图像
    :param image_shape:         原始图像的大小
    :param input_size:          输入图像的大小
    :return:
    """
    # image data
    image = PaddleTensor()
    image.name = 'image'
    image.shape = input_size
    image.dtype = PaddleDType.FLOAT32
    image.data = PaddleBuf(image_data.flatten().astype(np.float32).tolist())

    return image


def resize_img(img, target_size):
    """
    resize image
    :param img:
    :param target_size:
    :return:
    """
    img = img.resize(target_size[1:], Image.BILINEAR)
    return img


def crop_image(img, target_size): 
    '''
    crop_image
    :param img: input Image
    :param target_size: image resize target
    :return: resized image
    '''
    width, height = img.size  
    w_start = (width - target_size[2]) / 2  
    h_start = (height - target_size[1]) / 2  
    w_end = w_start + target_size[2]  
    h_end = h_start + target_size[1]  
    img = img.crop((w_start, h_start, w_end, h_end))  
    return img 
    
    
def read_image(image_bytes, target_size):
    """
    read image
    :param image_base64: input image, base64 encode string
    :param target_size: image resize target
    :return: origin image and resized image
    """
    start_time = time.time()
    # image_bytes = base64.b64decode(image_base64)
    img_array = np.fromstring(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.COLOR_RGB2BGR)
    origin = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    img = resize_img(origin, target_size)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    # img = np.array(img).astype(np.float32).transpose((2, 0, 1))  # HWC to CHW
    # img -= 127.5
    # img *= 0.007843
    mean_rgb = [127.5, 127.5, 127.5]  
    img = crop_image(img, target_size)  
    img = np.array(img).astype('float32')  
    img -= mean_rgb  
    img = img.transpose((2, 0, 1))  # HWC to CHW  
    img *= 0.007843
    img = img[np.newaxis,:]
    period = time.time() - start_time
    logger.info("read image base64 and resize cost time: {}".format("%2.2f sec" % period))
    return origin, img
