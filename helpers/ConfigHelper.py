import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 1)))
from helpers.FileHelper import FileHelper
from helpers.LogHelper import LogHelper


class ConfigHelper:
    """
    配置管理静态帮助类，提供获取配置项的功能。
    """
    _config = {
        "NEED_QUIT_RIGHTNOW": "NO"
    }

    @staticmethod
    def get(key, default=None):
        #从config.ini文件中读取配置项
        if not ConfigHelper._config:
            if os.path.exists("config.ini"):
                with open("config.ini", "r") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            ConfigHelper._config[k] = v 
        return ConfigHelper._config.get(key, default)
    
    
    @staticmethod
    def set(key, value):
        ConfigHelper._config[key] = value
        # 保存到config.ini文件
        with open("config.ini", "w") as f:
            for k, v in ConfigHelper._config.items():
                f.write(f"{k}={v}\n")



if __name__ == "__main__":
    LogHelper.info("Script running now ok")
    LogHelper.info("This is an info message.")
    LogHelper.debug("This is a debug message.")
    LogHelper.warning("This is a warning message.")
    LogHelper.error("This is an error message.")
    LogHelper.critical("This is a critical message.")
    LogHelper.info("创建的新 profile_id: %s", 222222222222)
    # 故意传错（无占位符，但传参数）
    LogHelper.info("测试错误格式化", 123, 456, "abc")
