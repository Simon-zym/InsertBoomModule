import logging
from logging import handlers
from pathlib import Path


class Logger:
    """
    雷赛工具链日志 — 同时输出到控制台与 logfiles/ 目录。

    show_level 控制控制台 verbosity，record_level 控制文件记录级别。
    """

    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'crit': logging.CRITICAL
    }

    def __init__(self,
                 filename,
                 level='info',
                 show_level='info',
                 record_level='info',
                 when='D',
                 backCount=3,
                 fmt='%(levelname)s - %(asctime)s - %(message)s'
                 ):
        """
         日志记录类
        :param filename: 日志文件名
        :param level:  日志级别
        :param show_level:  屏幕显示日志级别
        :param record_level:  日志文件记录日志级别
        :param when:  日志文件切割时间单位
        :param backCount:  日志文件保留个数
        :param fmt:  日志格式
        """

        self.logger = logging.getLogger(filename)
        self.logger.setLevel(self.level_relations.get(level))  # 设置日志级别
        self.logger.propagate = False

        if len(self.logger.handlers) > 0:
            return

        format_str = logging.Formatter(fmt)  # 设置日志格式
        Path(filename).parent.mkdir(exist_ok=True, parents=True)
        # 往文件里写入指定间隔时间自动生成文件的处理器, 实例化TimedRotatingFileHandler
        # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒、M 分、H 小时、D 天、W 每星期（interval==0时代表星期一）、midnight 每天凌晨
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)  # 设置文件里写入的格式
        th.setLevel(self.level_relations.get(record_level))  # 设置日志级别

        sh = logging.StreamHandler()  # 往屏幕上输出
        sh.setFormatter(format_str)  # 设置屏幕上显示的格式
        sh.setLevel(self.level_relations.get(show_level))  # 设置日志级别

        self.logger.addHandler(sh)  # 把对象加到logger里
        self.logger.addHandler(th)

    def info_show(self, info):
        self.logger.info(f": {info}")

    def error_show(self, error: str):
        self.logger.error(f": {error}")

    def finish_show(self, info: str):
        self.logger.critical(f": {info}")

    def warn_show(self, warn: str):
        self.logger.warning(f": {warn}")


if __name__ == '__main__':
    log = Logger('../all.log', level='debug')
    log.logger.debug('debug')
    log.logger.info('info')
    log.logger.warning('警告')
    log.logger.error('报错')
    log.logger.critical('严重')
    Logger('../error.log', level='error').logger.error('error')
