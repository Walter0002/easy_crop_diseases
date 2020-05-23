# -*- coding: utf-8 -*-
"""
logger utilities
"""
import uuid
import os
import logging.config
from threading import current_thread


# create default logger instance.
if not os.path.exists("logs"):
    os.mkdir("logs")

if not os.path.exists("logs/app-server.log"):
    f = open("logs/app-server.log", 'w')
    f.close()

if os.path.exists('conf/logger.conf'):
    logging.config.fileConfig('conf/logger.conf')
elif os.path.exists('../conf/logger.conf'):
    logging.config.fileConfig('../conf/logger.conf')
elif os.path.exists('../../conf/logger.conf'):
    logging.config.fileConfig('../../conf/logger.conf')
else:
    raise Exception("logger.conf not found!")


class LoggerWithLoggerId(logging.LoggerAdapter):

    def __init__(self, logger, extra):
        logging.LoggerAdapter.__init__(self, logger, extra)
        self.logid_dict = {}

    def set_auto_logid(self):
        self.logid_dict[current_thread().ident] = str(uuid.uuid4().int & (1 << 64) - 1)

    def set_logid(self, logid):
        self.logid_dict[current_thread().ident] = logid

    def get_logid(self):
        if current_thread().ident in self.logid_dict:
            return self.logid_dict[current_thread().ident]
        else:
            return None

    @property
    def level(self):
        return self.logger.level

    def process(self, msg, kwargs):
        if current_thread().ident in self.logid_dict:
            # in process thread
            if 'extra' not in kwargs:
                kwargs['extra'] = {'logid': self.logid_dict[current_thread().ident]}
            else:
                kwargs['extra']['logid'] = self.logid_dict[current_thread().ident]
        else:
            # in main loop thread
            if 'extra' not in kwargs:
                kwargs['extra'] = {'logid': 'react-main-loop-logid'}
            else:
                kwargs['extra']['logid'] = 'react-main-loop-logid'

        return msg, kwargs


logger = LoggerWithLoggerId(logging.getLogger('app-server'), {'logid': ''})
