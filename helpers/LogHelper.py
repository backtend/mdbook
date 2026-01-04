import logging
import sys
import os
from datetime import datetime
from logging import FileHandler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 1)))
from helpers.FileHelper import FileHelper
from libs.enved.enved import Enved


class DailyLevelFileHandler(FileHandler):
    """
    自定义文件 Handler：
    - 文件名格式：YYYY-MM-DD.level.log
    - 每天和每月自动切换新文件 / 新目录
    """

    # 修改后的 __init__ (只保留状态初始化，不打开文件)
    def __init__(self, level_name, formatter):
        self.level_name = level_name
        self.formatter = formatter
        self.current_date = datetime.now().date()
        self.current_year_month = datetime.now().strftime('%Y%m')
        self.log_dir = None # 保持延迟获取
        
        # 🌟 关键改动点：传入一个有效的占位符文件名，并设置 delay=True
        # 当 delay=True 时，FileHandler 不会在 __init__ 中打开文件。
        # 我们将在 _deferred_init 中设置正确的 self.baseFilename。
        super().__init__("/dev/null", mode='a', encoding='utf-8', delay=True) 

        self.setFormatter(formatter)
        self.setLevel(getattr(logging, level_name))
    # DailyLevelFileHandler 中新增的方法
    def _deferred_init(self):
        """首次写入日志时创建目录并打开文件"""
        # 只需要执行一次切换/打开文件的逻辑即可
        self._switch_file() # 🌟 调用 _switch_file 来完成初始化工作
        
    # 修改后的 emit
    def emit(self, record):
        """写日志时自动检测是否日期或月份变化，并处理首次打开文件"""
        # FileHandler 在 delay=True 时，self.stream 初始为 None
        if self.stream is None: 
            self._deferred_init() 

        now = datetime.now()
        if now.date() != self.current_date or now.strftime('%Y%m') != self.current_year_month:
            self._switch_file()
            
        super().emit(record)

    # 新增方法
    def _deferred_init(self):
        """延迟初始化：首次写入日志时创建目录并打开文件"""
        self.acquire()
        try:
            if self.stream is None:
                self.current_date = datetime.now().date()
                self.current_year_month = datetime.now().strftime('%Y%m')
                # 首次获取日志目录，这时才会创建目录
                self.log_dir = self._get_log_dir()
                new_filename = self._get_log_filename()
                self.baseFilename = os.path.abspath(new_filename)
                self.stream = self._open() # 打开文件流
        finally:
            self.release()
            
    def _switch_file(self):
        """关闭旧文件，切换到新的日期和月份对应的文件"""
        self.acquire()
        try:
            if self.stream:
                self.stream.close()

            self.current_date = datetime.now().date()
            self.current_year_month = datetime.now().strftime('%Y%m')
            self.log_dir = self._get_log_dir()

            new_filename = self._get_log_filename()
            self.baseFilename = os.path.abspath(new_filename)
            self.stream = self._open()
        finally:
            self.release()

    def _get_log_dir(self):
        """返回对应年月的日志目录，例如 runtime/log/202510/"""
        year_month = datetime.now().strftime('%Y%m')
        log_dir = FileHelper.runtime_path(os.path.join("log", year_month))
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def _get_log_filename(self):
        """生成 YYYY-MM-DD.level.log 格式的文件路径"""
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.{self.level_name.lower()}.log"
        return os.path.join(self.log_dir, filename)


class LogHelper:
    """
    日志记录静态帮助类
    规则：
      - 所有日志级别输出到控制台
      - INFO / WARNING / ERROR / CRITICAL 分级别写入文件
      - 文件名格式：YYYY-MM-DD.level.log
      - 月份切换自动进入新目录
    """
    _LOG_LEVEL = logging.DEBUG
    _logger = logging.getLogger("LogHelper")
    _initialized = False
    _handlers = {}

    @staticmethod
    def _initialize():
        if LogHelper._initialized:
            return

        LogHelper._logger.setLevel(LogHelper._LOG_LEVEL)
        LogHelper._logger.handlers = []

        formatter = logging.Formatter(
            '[%(asctime)s][%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S,%f'[:-3]
        )

        # 控制台 Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LogHelper._LOG_LEVEL)
        console_handler.setFormatter(formatter)
        LogHelper._logger.addHandler(console_handler)
        LogHelper._handlers['CONSOLE'] = console_handler

        # 不同级别文件 Handler
        for level in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            handler = DailyLevelFileHandler(level, formatter)
            handler.addFilter(lambda record, lvl=level: record.levelno == getattr(logging, lvl))
            LogHelper._logger.addHandler(handler)
            LogHelper._handlers[level] = handler

        LogHelper._initialized = True
        LogHelper._logger.debug("LogHelper initialized successfully.")

    @staticmethod
    def _safe_log(level, msg, *args, **kwargs):
        """安全日志输出，避免 string formatting 出错"""
        LogHelper._initialize()
        logger = LogHelper._logger

        try:
            if args:
                formatted_msg = msg % args
            else:
                formatted_msg = msg
        except Exception:
            formatted_msg = str(msg) + "\n" + "\n".join([str(a) for a in args])

        logger.log(level, formatted_msg, **kwargs)

    @staticmethod
    def debug(msg, *args, **kwargs):
        LogHelper._safe_log(logging.DEBUG, msg, *args, **kwargs)

    @staticmethod
    def info(msg, *args, **kwargs):
        LogHelper._safe_log(logging.INFO, msg, *args, **kwargs)

    @staticmethod
    def warning(msg, *args, **kwargs):
        LogHelper._safe_log(logging.WARNING, msg, *args, **kwargs)

    @staticmethod
    def error(msg, *args, **kwargs):
        LogHelper._safe_log(logging.ERROR, msg, *args, **kwargs)

    @staticmethod
    def critical(msg, *args, **kwargs):
        LogHelper._safe_log(logging.CRITICAL, msg, *args, **kwargs)


if __name__ == "__main__":
    LogHelper.info("程序启动")
    LogHelper.debug("调试信息")
    LogHelper.info("这是一条 info 日志")
    LogHelper.warning("这是一条 warning 日志")
    LogHelper.error("这是一条 error 日志")
    LogHelper.critical("这是一条 critical 日志")
    LogHelper.info("创建的新 profile_id: %s", 123456789)
    # 故意传错
    LogHelper.info("测试格式化错误", 111, 222)
