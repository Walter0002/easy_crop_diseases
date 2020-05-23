# -*- coding: utf-8 -*-
"""
manage executor
"""
import os
import shutil
import json

from paddle import fluid
from utils.logger_util import logger
from conf.server_conf import config

# get main version of python, maybe 3 or 2
import sys
PYTHON_VERSION = int(sys.version.split('.')[0])
if PYTHON_VERSION == 2:
    from Queue import Queue
    from Queue import Empty
else:
    from queue import Queue
    from queue import Empty
PRIVATE = 'private'


class ExecutorManager(object):
    """
    executor manager, hold a multi-thread safe queue
    worker threads compete to get executor
    """
    CPU_DEVICE = 'cpu'
    GPU_DEVICE = 'gpu'

    def __init__(self):
        """
        create executor manager
        """
        self.get_executor_timeout = float(config.get('get.executor.timeout', default_value=0.5))
        model_dir = config.get('model.dir')
        # 将地址的json字符串转为字典，key为模型的名称，value为模型的地址，放便级联使用
        model_dir = json.loads(model_dir)
        executor_count = 0
        enable_mkl = False
        gpu_memory = 200
        gpu_device_ids = []
        self.places_list = []

        # 模型的字典
        self.model_dict = {}
        for model_name in model_dir.keys():
            self._load_model(model_dir[model_name], model_name)

        device_type = config.get('device.type')
        if device_type == ExecutorManager.CPU_DEVICE:
            cpu_executor_count = int(config.getint('cpu.executor.count', default_value=0))
            executor_count = cpu_executor_count
        elif device_type == ExecutorManager.GPU_DEVICE:
            gpu_executor_count = int(config.getint('gpu.executor.count', default_value=0))
            executor_count = gpu_executor_count
            gpu_device_ids = config.get('gpu.executor.device.id').split(',')
            gpu_device_ids = map(int, gpu_device_ids)
            if PYTHON_VERSION == 3:
                gpu_device_ids = list(gpu_device_ids)
            assert len(gpu_device_ids) == gpu_executor_count, "gpu executor count doesn't match device count"
        else:
            raise Exception("no device to run executor!")
        assert executor_count > 0, "no device to predict"
        logger.info("device type:{} executor count:{} model dir:{} get executor timeout:{}s"
                    .format(device_type, executor_count, model_dir, self.get_executor_timeout))
        self.executor_queue = Queue(maxsize=executor_count)

        for i in range(executor_count):
            # executor is thread safe,
            # supports single/multiple-GPU running,
            # and single/multiple-CPU running,
            # if CPU device, only create one for all thread
            if device_type == ExecutorManager.CPU_DEVICE:
                if self.executor_queue.empty():
                    place = fluid.CPUPlace()
                    executor = fluid.Executor(place)
                    self._temp_executor = executor
                else:
                    executor = self._temp_executor
            else:
                device_id = gpu_device_ids[i]
                place = fluid.CUDAPlace(device_id)
                executor = fluid.Executor(place)

            self.executor_queue.put(executor)

    def get_executor(self):
        executor = None
        try:
            executor = self.executor_queue.get(block=True, timeout=self.get_executor_timeout)
        except Empty as e:
            logger.warning("current busy, can't get a executor")
        return executor

    def return_executor(self, executor):
        self.executor_queue.put(executor)

    def get_infer_stuff(self, model_name):
        """
        根据需要的模型名称来获取infer的信息，这里的模型名称对应config中的名称
        infer的信息，包括inference_program、feed_target_names、fetch_targets
        """
        inference_program, feed_target_names, fetch_targets = self.model_dict[model_name]
        return inference_program, feed_target_names, fetch_targets

    def _load_model(self, model_dir, model_name):
        """
        加载模型
        :param model_dir 模型存放的路径
        :param model_name 模型存放的名称
        """
        place = fluid.CPUPlace()
        exe = fluid.Executor(place)

        # print(os.getcwd())
        # print(model_dir)
        model_dir = os.path.join('H:\\useModel',model_dir)
        [inference_program, feed_target_names, fetch_targets] = fluid.io.load_inference_model(dirname=model_dir,
                                                                                              executor=exe)

        exe.close()
        self.model_dict[model_name] = [inference_program, feed_target_names, fetch_targets]


executor_manager = ExecutorManager()
