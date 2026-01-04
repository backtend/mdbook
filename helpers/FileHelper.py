# -*- coding: utf-8 -*-
import os
import shutil
import time

class FileHelper:
    """
    文件和目录辅助工具类
    静态方法调用，无需实例化
    """

    @staticmethod
    def create_dir(path: str, recursive: bool = False):
        """
        创建目录
        :param path: 目录路径
        :param recursive: 是否允许递归创建父目录，默认为 False
        :return: True/False 表示是否创建成功或已存在
        """
        try:
            if recursive:
                os.makedirs(path, exist_ok=True)
            else:
                if not os.path.exists(path):
                    os.mkdir(path)
            
            if os.path.exists(path) and os.path.isdir(path):
                print(f"✅ 目录创建成功或已存在: {path}")
                return True
            else:
                print(f"❌ 目录创建失败: {path}")
                return False
        except Exception as e:
            print(f"❌ 创建目录出错: {path}，错误: {e}")
            return False

    @staticmethod
    def copy_file_or_dir(src: str, dst: str):
        """
        复制文件或目录
        :param src: 源文件/目录
        :param dst: 目标文件/目录
        :return: True/False 表示复制是否成功
        """
        if not os.path.exists(src):
            print(f"❌ 源路径不存在: {src}")
            return False

        try:
            if os.path.isfile(src):
                # 如果目标目录不存在，先创建
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"✅ 文件复制从: {src}")
                print(f"✅ 文件复制到: {dst}")
                print(f"✅ 文件复制完毕$$$$$$")
            elif os.path.isdir(src):
                # 复制目录下所有文件和子目录
                if not os.path.exists(dst):
                    os.makedirs(dst, exist_ok=True)
                for item in os.listdir(src):
                    sub_src = os.path.join(src, item)
                    sub_dst = os.path.join(dst, item)
                    FileHelper.copy_file_or_dir(sub_src, sub_dst)
                print(f"✅ 目录复制从: {src}")
                print(f"✅ 目录复制到: {dst}")
                print(f"✅ 目录复制完毕!!!!!!")
            else:
                print(f"❌ 跳过非文件/目录项: {src}")
                return False
            return True
        except Exception as e:
            print(f"❌ 复制失败: {src} -> {dst}，错误: {e}")
            return False

    @staticmethod
    def assets_path(*subdirs: str) -> str:
        """
        构建基于 ../assets 的路径，兼容 Windows 和 Unix 系统
        :param subdirs: 子目录，可传入多个参数
        :return: 拼接后的路径
        """
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        joined_path = os.path.join(base_path, *subdirs)
        return os.path.normpath(joined_path)

    @staticmethod
    def runtime_path(*subdirs: str) -> str:
        """
        构建基于 ../runtime 的路径，兼容 Windows 和 Unix 系统
        :param subdirs: 子目录，可传入多个参数
        :return: 拼接后的路径
        """
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "runtime"))
        return os.path.normpath(os.path.join(base_path, *subdirs))



if __name__ == "__main__":
    # 测试创建目录
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    test_dir = FileHelper.runtime_path("tmp", f"env_file_tmpdir_{timestamp}")
    FileHelper.create_dir(test_dir, recursive=True)

    # 测试复制文件
    test_txt = FileHelper.assets_path("default", "hey.txt")  # 确保这个目录存在
    dist_txt = FileHelper.runtime_path("tmp", f"copied_test_{timestamp}.txt")
    FileHelper.copy_file_or_dir(test_txt, dist_txt)

    # 测试复制目录
    test_src_dir = FileHelper.assets_path("adspower", "env_files")  # 确保这个目录存在
    copied_dir = FileHelper.runtime_path("tmp", f"copied_env_files_{timestamp}")
    FileHelper.copy_file_or_dir(test_src_dir, copied_dir)


