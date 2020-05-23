# -*- coding: utf-8 -*-
"""
consumer
"""
import threading
import business_service


class InferConsumer(threading.Thread):
    """
    消费者，用于从任务队列中获取需要预测的任务并组成一个batch，进行推断，并将
    推断结果返回给结果数组
    """

    def __init__(self, pivot, timeout):
        """
        初始化
        :param pivot:        任务-结果数据结构
        :param timeout:      获取任务时的最长等待时间，如果到达该时间，就算任务队列不满，也需要开始执行任务
        :return:
        """
        super(InferConsumer, self).__init__()
        self.pivot = pivot
        self.timeout = timeout

    def run(self):
        """
        获取任务并返回结果
        :return:
        """
        while True:
            task_list = self.pivot.get_task_queue(self.timeout)
            # 进行推断，并返回结果
            result = business_service.business_process(task_list)
            self.pivot.set_result_list(result)
