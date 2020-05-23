# -*- coding: utf-8 -*-
"""
业务相关的写在这里
"""
import numpy as np
import time
import sys
EXECUTOR = 'executor'
PREDICTOR = 'predictor'

from conf.server_conf import config
from utils.logger_util import logger
import utils.data_util as data_util
infer_type = config.get('predictor_or_executor')

if PREDICTOR == infer_type:
    from infer_service import infer_with_predictor
elif EXECUTOR == infer_type:
    from infer_service import infer_with_executor
PYTHON_VERSION = int(sys.version.split('.')[0])


def business_process(inputs):
    """
    不同业务，数据处理的方式可能不一样，统一在这里修改和控制
    为了充分利用多线程并行的方式来处理数据，所以首先由生产者调用process_data来处理数据，并提交至任务队列
    此处直接从任务队列中获取处理好的数据即可，因此该部分应该和process_data一起修改
    :param inputs:      从任务队列中获取的预处理后的数据
    :return:
    """

    if PREDICTOR == infer_type:
        outputs = infer_with_predictor(inputs)
        return outputs
    elif EXECUTOR == infer_type:
        # 重组数据
        image_data = [data[0] for data in inputs]
        image_data = np.array(image_data)

        start_time = time.time()
        # 通过不同的model名称来调用模型级联任务中 不同阶段需要用到的模型
        outputs = infer_with_executor("SE_ResNeXt", image_data)
        period = time.time() - start_time
        infer_num = image_data.shape[0]
        logger.info(
            "executor infer num {} cost time: {}".format(str(infer_num), "%2.2f sec" % period))
        outputs = np.array(outputs[0])
        result = []

        for lod_id in range(infer_num):
            data = {}
            output_data = outputs[lod_id]
            # logger.debug("executor infer result {}".format(output_data))
            data["result"] = np.array(output_data).tolist()
            # 首先先根据每次infer的output的lod信息，把output拆成一个图一个图的result
            result.append(data)
        return result
    else:
        logger.critical("must set a infer type in config, executor or predictor")
        exit(1)


def process_data(image_bytes):
    """
    根据infer_type来处理数据，并返回, 可根据业务需要自行修改
    :param inputs:    原始的输入数据
    :return:
    """
    # 两种方式 处理数据公共的部分
    input_size = config.get('input.size').split(',')
    input_size = map(int, input_size)
    if PYTHON_VERSION == 3:
        input_size = list(input_size)
    start_time = time.time()
    origin, image_data = data_util.read_image(image_bytes, input_size[1:])
    # 如果是predictor，需要进一步的把数据处理为PaddleTensor
    if PREDICTOR == infer_type:
        image_data = data_util.warp_input(image_data, input_size)
    period = time.time() - start_time
    logger.info("prepare input cost time: {}".format("%2.2f sec" % period))
    return image_data
