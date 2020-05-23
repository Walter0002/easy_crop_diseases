# -*- coding: utf-8 -*-
"""
infer service, just an example
"""
import numpy as np
import time
# get main version of python, maybe 3 or 2
import sys

PYTHON_VERSION = int(sys.version.split('.')[0])
EXECUTOR = 'executor'
PREDICTOR = 'predictor'

from conf.server_conf import config
from utils.logger_util import logger

infer_type = config.get('predictor_or_executor')
if PREDICTOR == infer_type:
    from predict.predictor_manager import predictor_manager
elif EXECUTOR == infer_type:
    from predict.executor_manager import executor_manager


def infer_with_predictor(input):
    """
    infer a image with predictor, for example
    :param input: image base64
    :return: pred out
    """
    start_time = time.time()
    period = time.time() - start_time
    logger.info("warp_input cost time: {}".format("%2.2f sec" % period))
    predictor = predictor_manager.get_predictor()
    if predictor is not None:
        try:
            start_time = time.time()
            outputs = predictor.run(input)
            period = time.time() - start_time
            logger.info("predictor infer cost time: {}".format("%2.2f sec" % period))
            if len(outputs) > 0:
                output = outputs[0]
                print(output.name)
                output_data = np.array(output.data.float_data())
                output_data = output_data.reshape(-1, 6)
                # logger.debug("predictor infer result {}".format(output_data))
                return output_data.tolist()
            return "infer nothing"
        finally:
            predictor_manager.return_predictor(predictor)
    else:
        return None


def infer_with_executor(model_name, infer_data, *args):
    """
    infer with executor, infer_data和后续的参数顺序必须严格遵守模型固化时指定的顺序
    :param model_name: 需要进行infer的模型名字
    :param infer_data:
    :param *args:
    :return:
    """
    inference_program, feed_target_names, fetch_targets = executor_manager.get_infer_stuff(model_name)
    if len(args) + 1 != len(feed_target_names):
        logger.warning("infer param not match model requirement! require params: {}".format(feed_target_names))
        raise ValueError("infer param not match model requirement! require params: {}".format(feed_target_names))
    infer_dict = {feed_target_names[0]: infer_data}
    for idx, param in enumerate(args):
        infer_dict[feed_target_names[idx + 1]] = param
    executor = executor_manager.get_executor()
    if executor is not None:
        try:
            outputs = executor.run(inference_program,
                                   feed=infer_dict,
                                   fetch_list=fetch_targets,
                                   return_numpy=False)
        finally:
            executor_manager.return_executor(executor)
        return outputs
    else:
        return None
