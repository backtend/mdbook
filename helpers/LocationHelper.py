import logging
import os, sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 1)))


class LocationHelper:
    """
    LocationHelper 类用于处理坐标转换和截图相关的操作。\
    """


    @staticmethod
    def convert_coordinates(x: int, y: int, shape, viewport_size) -> tuple:
        """
        把截图分辨率下的坐标转换成实际页面坐标

        Args:
            x (int): 模板匹配得到的 x 坐标（基于截图）
            y (int): 模板匹配得到的 y 坐标（基于截图）
            shot_img: cv2.imread 读取的截图对象
            page (Page): Playwright 的 Page 对象，用于获取 viewport

        Returns:
            (int, int): 转换后的 (x, y) 坐标，基于页面实际 viewport
        """
        if shape is None:
            raise ValueError("shape 不能为空")

        shot_h, shot_w = shape[:2]

        page_w, page_h = viewport_size["width"], viewport_size["height"]

        real_x = int(x * page_w / shot_w)
        real_y = int(y * page_h / shot_h)

        return real_x, real_y