# libs/enved/enved.py

import os
import sys
from pathlib import Path

def _resolve_dotenv_path():
    # 如果是打包环境（PyInstaller），使用 _MEIPASS 路径
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / '.env'
    # 否则使用源码路径（开发环境）
    return Path(__file__).parent.parent.parent / '.env'

_dotenv_path = _resolve_dotenv_path()
_env_vars = None  # 使用 None 来表示变量尚未加载


# 使用 pathlib 找到项目的根目录，然后加载并解析 .env 文件。
# __file__ 指向当前文件 (libs/enved/enved.py)
# .parent.parent.parent 向上三级目录到达项目根目录
# _dotenv_path = Path(__file__).parent.parent.parent / '.env'
# _env_vars = None  # 使用 None 来表示变量尚未加载

class Enved:
    """
    环境处理类。
    提供了静态方法来获取和判断当前应用的环境标签。
    """
    
    @staticmethod
    def _load_dotenv_manual():
        """
        私有静态方法：手动加载和解析 .env 文件。
        这个方法只在需要时被调用一次。
        """
        global _env_vars
        _env_vars = {}
        try:
            with open(_dotenv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 去除每行首尾的空白字符
                    line = line.strip()
                    # 忽略空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 分割键和值
                    if '=' in line:
                        key, value = line.split('=', 1)
                        _env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            # 如果 .env 文件不存在，则不进行任何操作
            pass
        except Exception as e:
            # 捕获其他可能的异常，例如文件编码问题
            print(f"解析 .env 文件时发生错误: {e}")
    
    @staticmethod
    def tag() -> str:
        """
        获取环境标签。
        如果环境变量 APP_ENVED 未设置，则默认为 'dev'。
        """
        global _env_vars
        # 懒加载：如果环境变量字典尚未加载，则先进行加载
        if _env_vars is None:
            Enved._load_dotenv_manual()
        
        # 从手动加载的字典中获取值，如果不存在则使用 os.getenv()
        # 作为 fallback，最后默认为 'dev'。
        return _env_vars.get('APP_ENVED', os.getenv('APP_ENVED', 'dev'))

    @staticmethod
    def value(key: str, default: str = None) -> str:
        """
        根据键获取环境变量的值。
        如果键不存在，则返回默认值。
        """
        global _env_vars
        # 懒加载：如果环境变量字典尚未加载，则先进行加载
        if _env_vars is None:
            Enved._load_dotenv_manual()
        
        # 从手动加载的字典中获取值，如果不存在则使用 os.getenv()
        return _env_vars.get(key, os.getenv(key, default))

    @staticmethod
    def isDev() -> bool:
        """
        判断当前环境是否为 'dev'。
        """
        return Enved.tag() == 'dev'
    
    @staticmethod
    def notDev() -> bool:
        """
        判断当前环境是否不是 'dev'。
        """
        return not Enved.isDev()
    
    @staticmethod
    def isBox() -> bool:
        """
        判断当前环境是否为 'box'。
        """
        return Enved.tag() == 'box'

    @staticmethod
    def notBox() -> bool:
        """
        判断当前环境是否不是 'box'。
        """
        return not Enved.isBox()

    @staticmethod
    def isTest() -> bool:
        """
        判断当前环境是否为 'test'。
        """
        return Enved.tag() == 'test'
        
    @staticmethod
    def notTest() -> bool:
        """
        判断当前环境是否不是 'test'。
        """
        return not Enved.isTest()

    @staticmethod
    def isPre() -> bool:
        """
        判断当前环境是否为 'pre'。
        """
        return Enved.tag() == 'pre'

    @staticmethod
    def notPre() -> bool:
        """
        判断当前环境是否不是 'pre'。
        """
        return not Enved.isPre()

    @staticmethod
    def isProd() -> bool:
        """
        判断当前环境是否为 'prod'。
        """
        return Enved.tag() == 'prod'
        
    @staticmethod
    def notProd() -> bool:
        """
        判断当前环境是否不是 'prod'。
        """
        return not Enved.isProd()

    @staticmethod
    def prod(prod_val, else_val):
        """
        如果当前环境为 'prod'，则返回 prod_val；否则返回 else_val。
        """
        return prod_val if Enved.isProd() else else_val

    @staticmethod
    def isOnline() -> bool:
        """
        判断当前环境是否为线上环境。
        我们假设只有 'prod' 是线上环境。
        """
        return Enved.tag() == 'prod'
        
    @staticmethod
    def isOffline() -> bool:
        """
        判断当前环境是否为非线上环境。
        """
        return not Enved.isOnline()
    

# --- 示例用法 (这段代码不会在导入时执行) ---
if __name__ == '__main__':
    print(f"当前环境标签是: {Enved.tag()}")
    print(f"是开发环境吗? {Enved.isDev()}")
    print(f"是线上环境吗? {Enved.isProd()}")
    print(f"远程API路径前缀? {Enved.value('API_URL_PREFIX')}")

    # 使用 prod() 方法
    value_to_use = Enved.prod("线上值", "非线上值")
    print(f"使用 prod() 方法得到的值是: {value_to_use}")
