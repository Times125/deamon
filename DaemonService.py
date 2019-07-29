#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author: _defined
@Time:  2019/7/24 15:43
@Description: python程序守护进程,可以动态加载配置文件
"""
import os
import time
import yaml
import psutil
import json
import operator
import subprocess
import threading
from watchdog.events import *
from watchdog.observers import Observer
from logger import daemon_logger

# 每10秒检查一下程序是否正常运行
check_interval = 10


def load_config():
    """
    载入配置文件
    :return:
    """
    yaml_path = os.path.join(os.path.dirname(__file__), 'sys_config.yaml')
    with open(yaml_path, encoding='utf-8') as f:
        yaml_cont = f.read()
    cf = yaml.load(yaml_cont, Loader=yaml.SafeLoader)
    return cf


class DaemonService(object):
    def __init__(self):
        self.cf = load_config()
        self.info = None
        self.is_reload_config = False  # 暂时没什么用

    @classmethod
    def start_program(cls, name, directory, cmdline, pid_file, logfile, left_time):
        """
        启动程序
        :param name:程序名
        :param directory:运行目录
        :param cmdline: 运行命令
        :param pid_file: pid文件路径
        :param logfile: log文件路径
        :param left_time: 剩余失败重启尝试次数
        :return:
        """
        s = None
        if left_time == 0:
            return
        try:
            with open(logfile, 'wb') as fp:  # subprocess.DEVNULL
                s = subprocess.Popen(cmdline, cwd=directory, stdout=fp.fileno(), stderr=fp.fileno())
            daemon_logger.info('########### 程序 {} 启动成功，pid为{} ###########'.format(name, s.pid))
        except (OSError, FileNotFoundError) as e:
            daemon_logger.error('启动程序 {} 失败, 请检查配置是否正确'.format(name))
            daemon_logger.exception(e)
        finally:
            info = {'pid': s.pid if s else -1, 'cmdline': cmdline, 'left_time': left_time - 1 if left_time > 0 else -1}
            with open(pid_file, 'w+', encoding='utf8') as fp:
                fp.write(json.dumps(info))

    def supervisor(self):
        """
        监控程序是否正常运行
        :return:
        """
        for name, attrs in self.cf.items():
            try:
                directory = attrs.get('directory', '').replace(os.sep, '/')
                cmdline = [i for i in attrs.get('cmdline', '').replace(os.sep, '/').split() if i]
                retires = attrs.get('retries', -1)
                logfile = attrs.get('logfile', '').replace(os.sep, '/')
                pid_file = os.path.join(directory, name + '.pid')
                if os.path.isfile(pid_file):
                    with open(pid_file, 'r+') as fp:
                        self.info = json.load(fp)  # 加载程序的pid文件
                    if retires == -1:  # 不限制失败重启的次数
                        if not self.is_running():  # 如果程序没有运行就启动
                            self.start_program(name, directory, cmdline, pid_file, logfile, retires)
                    else:  # 限制失败重启的次数
                        # 如果上次配置是不限制重启次数，修改配置后限制重启次数，则需重置剩余次数
                        if self.info['left_time'] == -1:
                            self.info['left_time'] = retires
                        if self.info['left_time'] > 0 and not self.is_running():  # 检查剩余失败重启次数
                            self.start_program(name, directory, cmdline, pid_file, logfile, self.info['left_time'])
                # TODO 这里存在一个问题，如果移动或者删除pid文件后，将会启动新的程序副本（原来的程序并没有退出）
                else:
                    self.start_program(name, directory, cmdline, pid_file, logfile, retires)
            except Exception as e:
                daemon_logger.exception(e)

    def supervisor2(self):
        pass

    def is_running(self):
        """
        检查程序是否运行
        :return:
        """
        if psutil.pid_exists(self.info['pid']):
            p = psutil.Process(self.info['pid'])
            # print(p.cmdline(),'===',self.info['cmdline'])
            if operator.eq(p.cmdline(), self.info['cmdline']):
                return True
        else:
            return False

    def reload_config(self):
        """
        重新载入配置文件
        :return:
        """
        self.is_reload_config = True
        self.cf = load_config()

    @classmethod
    def status(cls, pid):
        """
        检查程序状态
        :param pid:
        :return:
        """
        if psutil.pid_exists(pid):
            return psutil.Process(pid).status()

    @classmethod
    def stop(cls, pid):
        """
        停止指定进程
        :param pid:
        :return:
        """
        if psutil.pid_exists(pid):
            psutil.Process(pid).kill()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        super(FileEventHandler, self).__init__()

    def on_modified(self, event):
        if event.is_directory:
            pass
        else:
            if event.src_path.endswith('sys_config.yaml'):
                service.reload_config()


def event_loop():
    even_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(even_handler, os.path.curdir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


threading.Thread(target=event_loop, daemon=True).start()

if __name__ == '__main__':
    daemon_logger.info('########### 守护程序启动... ########### ')
    service = DaemonService()
    while True:
        service.supervisor()
        time.sleep(check_interval)
