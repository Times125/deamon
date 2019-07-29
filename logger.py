#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author:_defined
@Time:  2018/8/28 19:52
@Description: 
"""
import os
import logging
from logging import config as log_conf

__all__ = ["daemon_logger", ]


abs_path = os.path.join(os.path.dirname(__file__), 'DaemonLogs')
if not os.path.exists(abs_path):
    os.mkdir(abs_path)
log_path = os.path.join(abs_path, 'daemon.log')
# print(abs_path)
log_config = {
    'version': 1.0,
    'formatters': {
        'detail': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '%(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detail'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 10,
            'filename': log_path,
            'level': 'INFO',
            'formatter': 'detail',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'daemon_logger': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    }
}

log_conf.dictConfig(log_config)

daemon_logger = logging.getLogger("daemon_logger")
