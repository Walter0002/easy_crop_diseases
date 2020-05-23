# -*- coding: utf-8 -*-
"""
实现一个数据结构，包含任务队列和结果数组
"""
import sys
import time
import threading
from utils.logger_util import logger
PYTHON_VERSION = int(sys.version.split('.')[0])


class Pivot(object):
    """
    生产者和消费者数据沟通的枢纽
    """
    def __init__(self, task_num):
        """
        初始化任务队列和结果数组
        :param task_num:      任务队列的最大长度
        """
        self.task_queue = [None for _ in range(task_num)]
        self.task_queue_index = 0
        self.result_list = [None for _ in range(task_num)]
        # 这个锁是用来任务队列读写的
        self.q_lock = threading.Lock()
        # 这个锁是用来在任务队列满了的时候把自己塞住的, 初始的时候是开着的，当任务队列满了的时候，锁住
        self.q_full = threading.Event()
        self.q_full.set()
        # 这个锁是用来控制阻塞的从结果数组获取结果的
        self.r_lock = threading.Condition()
        # 这个锁是用来唤醒消费者过来消费的
        self.c_lock = threading.Event()
        self.task_num = task_num

    def set_task_queue(self, data, timeout=0.5):
        """
        用于生产者向队列中提交任务，并返回对应的索引位置
        :param data:     需要提交的数据
        :param timeout:  最长等待时间
        :return:         生产者到时候需要在结果数组中获取结果的索引
        """
        index = None
        # 这里如果查询放在锁外面有概率造成，请求提前结束等待，然后返回请求超时,所以查询的时候也需要加锁，
        # 如果目前队列满，那么先解锁，然后等待，然后加锁再次尝试添加数据，如果还是不行，就超时
        self.q_lock.acquire()
        if not self.q_full.is_set():
            self.q_lock.release()
            self.q_full.wait(timeout)
            self.q_lock.acquire()
        if self.q_full.is_set():
            index = self.task_queue_index
            self.task_queue[index] = data
            self.task_queue_index += 1
            # 如果消费者还没被唤醒，那就唤醒他
            if not self.c_lock.is_set():
                self.c_lock.set()

            # 如果任务队列满了，夯住自己
            if self.task_queue_index == self.task_num:
                self.q_full.clear()
        else:
            logger.info("set:task_queue is full, try a moment later")
        self.q_lock.release()
        return index

    def get_task_queue(self, timeout=0.01):
        """
        用于消费者从任务队列中获取任务
        :param timeout:     最长等待时间，就像班车，要么人满发车，要么到时间发车
        :return:     任务队列
        """
        # 首先没有任务提交之前，先被阻塞，静静的等待第一个任务的到来
        self.c_lock.wait()
        start_time = time.time()
        while time.time() - start_time <= timeout:
            if self.task_queue_index != self.task_num:
                continue
            else:
                break
        self.q_lock.acquire()
        task_list = self.task_queue[0:self.task_queue_index]
        # 由于预测任务开始，这里不管满不满都应该设置为满，防止新任务提交造成任务丢失
        self.task_queue_index = self.task_num
        self.q_full.clear()

        self.q_lock.release()
        return task_list

    def set_result_list(self, infer_result):
        """
        用于返回结果
        :param infer_result:    推断结果
        :return:
        """
        result_len = len(infer_result)
        for index in range(result_len):
            self.result_list[index] = infer_result[index]
        self.r_lock.acquire()
        # 唤醒等待中的线程，来从结果数组中获取数据
        self.r_lock.notify_all()
        self.r_lock.release()
        # 将任务队列置为空, 并通知生产者队列空了！！，可以继续了
        self.task_queue_index = 0
        self.q_full.set()
        # 执行完了，按照惯例 自己把自己夯住,下次获取数据的时候继续等数据来唤醒自己
        self.c_lock.clear()

    def get_result_list(self, index):
        """
        阻断的从任务队列中获取结果
        :param index:           结果的在数据中的索引
        :return:                返回结果
        """
        self.r_lock.acquire()
        # 阻塞，等待结果数组更新后，被唤醒
        self.r_lock.wait()
        result = self.result_list[index]
        self.r_lock.release()
        return result
