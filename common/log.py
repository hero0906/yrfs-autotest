#coding=utf-8
import logging
from logging import config
import os
from config import consts



"""
指定保存日志的文件路径，日志级别，以及调用文件
将日志存入到指定的文件中
"""
def log_setup():

    if not os.path.exists(consts.LOG_PATH):
        os.makedirs(consts.LOG_PATH)

    LOG_SETTINGS = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': '%s/autotest.log'%consts.LOG_PATH,
                'mode': 'a',
                'maxBytes': 10485760,
                'backupCount': 5,
            },

        },
        'formatters': {
            'detailed': {
                'format': '%(asctime)s %(levelname)s %(funcName)s:%(lineno)d %(message)s',
            },
            'email': {
                'format': 'Timestamp: %(asctime)s\nModule: %(module)s\n'
                'Line: %(lineno)d\nMessage: %(message)s',
            },
        },
        'loggers': {
            'autotest': {
                'level': 'DEBUG',
                'handlers': ['file', 'console']
                },
        }
    }

    config.dictConfig(LOG_SETTINGS)
    logger = logging.getLogger("autotest_script")
    return logger