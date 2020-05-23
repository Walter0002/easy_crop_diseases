# -*- coding: utf-8 -*-
"""
config
"""
import configparser
import os

from utils.logger_util import logger


class ServerConfig(object):
    """
    A util class encapsulate configuration operation
    """
    env = None

    def __init__(self, conf_path=None):

        if conf_path is None:
            # 默认路径检测
            if os.path.exists('conf/server.conf'):
                self.conf_path = 'conf/server.conf'
            elif os.path.exists('../conf/server.conf'):
                self.conf_path = '../conf/server.conf'
            elif os.path.exists('../../conf/server.conf'):
                self.conf_path = '../../conf/server.conf'
            else:
                raise Exception("server.conf not found!")
        else:
            self.conf_path = conf_path
        self.cf = configparser.ConfigParser()
        self.cf.read(self.conf_path, encoding='utf8')

    @classmethod
    def init_evn(cls, current_evn):
        """
        init config environment, and only once
        :param current_evn:
        :return:
        """
        if cls.env is None:
            cls.env = current_evn
        logger.info("current config section %s", cls.env, extra={'logid': 'react-main-loop-logid'})

    @classmethod
    def current_evn(cls):
        """
        get current environment
        :return:
        """
        return cls.env

    def get(self, key, default_value=None):
        """
        get configured value for a given key
        :param key: the key
        :param default_value: the default value if no entry is configured
        :return: the value
        """
        value = self.cf.get(ServerConfig.env, key)
        if value is None and default_value is not None:
            return default_value

        return value

    def getboolean(self, key, default_value=None):
        """
        get configured value for a given key
        :param key: the key
        :param default_value: the default value if no entry is configured
        :return: the value
        """
        value = self.cf.getboolean(ServerConfig.env, key)
        if value is None and default_value is not None:
            return default_value

        return value

    def getint(self, key, default_value=None):
        """
        get config value for given key
        :param key:
        :param default_value:
        :return:
        """
        value = self.cf.getint(ServerConfig.env, key)
        if value is None and default_value is not None:
            return default_value

        return value


# create default config instance
config = ServerConfig()
