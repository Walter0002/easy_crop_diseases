# -*- coding: utf-8 -*-
"""
manage predictor
"""
import os
import shutil

from utils.logger_util import logger
from conf.server_conf import config
from paddle.fluid.core import AnalysisConfig
from paddle.fluid.core import create_paddle_predictor

# get main version of python, maybe 3 or 2
import sys
PYTHON_VERSION = int(sys.version.split('.')[0])
if PYTHON_VERSION == 2:
    from Queue import Queue
    from Queue import Empty
else:
    from queue import Queue
    from queue import Empty


class PredictorManager(object):
    """
    predictor manager, hold a multi-thread safe queue
    worker threads compete to get predictor
    """
    CPU_DEVICE = 'cpu'
    GPU_DEVICE = 'gpu'

    def __init__(self):
        """
        create predictor manager
        """
        self.get_predictor_timeout = float(config.get('get.predictor.timeout', default_value=0.5))
        predictor_count = 0
        enable_mkl = False
        gpu_memory = 200
        gpu_device_ids = []

        model_dir = config.get('model.dir')
        device_type = config.get('device.type')
        if device_type == PredictorManager.CPU_DEVICE:
            cpu_predictor_count = int(config.getint('cpu.predictor.count', default_value=0))
            predictor_count = cpu_predictor_count
            enable_mkl = config.getboolean('cpu.enable_mkl', default_value=False)
        elif device_type == PredictorManager.GPU_DEVICE:
            gpu_predictor_count = int(config.getint('gpu.predictor.count', default_value=0))
            predictor_count = gpu_predictor_count
            gpu_memory = config.getint('gpu.predictor.memory', default_value=200)
            gpu_device_ids = config.get('gpu.predictor.device.id').split(',')
            gpu_device_ids = map(int, gpu_device_ids)
            if PYTHON_VERSION == 3:
                gpu_device_ids = list(gpu_device_ids)
            assert len(gpu_device_ids) == gpu_predictor_count, "gpu predictor count doesn't match device count"
        else:
            raise Exception("no device to run predictor!")
        assert predictor_count > 0, "no device to predict"
        logger.info("device type:{} predictor count:{} model dir:{} get predictor timeout:{}s"
                    .format(device_type, predictor_count, model_dir, self.get_predictor_timeout))
        self.predictor_queue = Queue(maxsize=predictor_count)

        for i in range(predictor_count):
            # Set config
            predictor_config = AnalysisConfig(model_dir)
            # predictor_config.specify_input_name()
            if device_type == PredictorManager.CPU_DEVICE:
                predictor_config.disable_gpu()
                if enable_mkl:
                    predictor_config.enable_mkldnn()
            else:
                device_id = gpu_device_ids[i]
                predictor_config.enable_use_gpu(gpu_memory, device_id)

            # Create PaddlePredictor
            predictor = create_paddle_predictor(predictor_config)
            self.predictor_queue.put(predictor)


    def get_predictor(self):
        predictor = None
        try:
            predictor = self.predictor_queue.get(block=True, timeout=self.get_predictor_timeout)
        except Empty as e:
            logger.warning("current busy, can't get a predictor")
        return predictor

    def return_predictor(self, predictor):
        self.predictor_queue.put(predictor)


predictor_manager = PredictorManager()
