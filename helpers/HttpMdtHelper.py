import os, sys
import base64
import hashlib
import json
import platform
import uuid
import random
import string
import time
import requests


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 1)))
from libs.enved.enved import Enved
from helpers.LogHelper import LogHelper
from libs.mariadb.models import Email  # 导入 Email 模型

"""
MDT请求帮助类
code非200的情况绝对会抛异常的形式！！！！！！！！
最后更新：2025-11-08 11:11:11
"""
class HttpMdtHelper:
    BASE_URL = Enved.value("PROJECT_MDT_URL")

    @staticmethod
    def post(url, data, options=None):
        """
        发送POST请求，支持自定义headers，支持文件/文件数组上传。
        :param url: 请求URL（可相对或绝对）
        :param data: 请求体，可以包含普通字段，也可以包含文件对象或文件列表
        :param options: 额外的请求选项
        :return: dict 响应结果
        """
        headers = {
            "Authorization": 'Token {}'.format(HttpMdtHelper.generate_authorization()),
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        # 合并用户传入的 headers
        if options and "headers" in options:
            headers.update(options["headers"])

        timeout = options["timeout"] if options and "timeout" in options else 15

        payload = data.copy()

        # 判断是否有文件
        files = None
        if "upload_file" in payload:
            files = {"upload_file": payload.pop("upload_file")}
            headers.pop("Content-Type", None)  # requests 会自动处理 multipart
        elif "upload_files" in payload:
            files = [("upload_files[]", f) for f in payload.pop("upload_files")]
            headers.pop("Content-Type", None)

        url = url if url.startswith("http") else f"{HttpMdtHelper.BASE_URL}{url.lstrip('.')}"
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload if not files else None,
                data=payload if files else None,
                files=files,
                timeout=timeout,
                verify=True
            )
        except requests.RequestException as e:
            raise Exception(f"HTTP请求失败: {e}")

        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}, 原因: {response.text}")

        response.raise_for_status()
        # print(url, response.text)  # 调试输出完整响应文本
        try:
            code = response.json().get("code")
            if code != 200:
                raise Exception(f"请求失败，响应码: {code}, 原因: {response.text}")
            
            data = response.json().get("data", {"code": 500, "msg": "响应数据格式错误-data缺失"})
        except json.JSONDecodeError:
            raise Exception(f"非JSON响应: {response.text}")

        return data
    

    '''
    # 授权头生成
    '''
    def generate_authorization():
        """
        生成双重MD5 + base64 的 Authorization 字段。
        """
        timestamp = str(int(time.time()))
        # timestamp = "1763628248" # 测试固定时间戳

        raw = Enved.value("PROJECT_MDT_SECRET") + timestamp
        md5_1 = hashlib.md5(raw.encode()).hexdigest()
        md5_2 = hashlib.md5(md5_1.encode()).hexdigest()

        merged = f"{md5_2},{timestamp}"
        encoded = base64.b64encode(merged.encode()).decode()

        return encoded


if __name__ == "__main__":
    # 示例参数，可根据实际接口要求修改
    payload = {"aaa": "bbb", "ccc": 123}
    payload = {"username": "test", "password": "123456"}

    eid = 177
    email = Email.get_or_none(Email.id == eid)
    # 进行推送操作
    LogHelper.info(f"📤 INFO: 开始推送邮件通知，邮件 ID: {email.id}")

    payload = {
        # "email_id": email.id,
        # "email_uuid": email.uuid,
        "senter_nickname": "snickname",
        "senter_username": "susername",
        "senter_domain": email.sender_domain,
        "senter_address": email.sender_address,
        "to_addresses": email.rcpter_address,
        # "cc_addresses": "\"李四\" <cc_user@sunrate.city>",
        # "bcc_addresses": "\"王五\" <bcc_user@sunrate.city>",
        "subject": email.subject,
        "content": email.content,
        "content_view": email.content,
        "content_size": len(email.content),
        "content_type": "text/html",
        "content_charset": "utf-8",
        # "sent_at": email.received_at,
    }

    # # 普通 JSON 请求：
    # https://unionapi.vaehub.com/index/receive/index?cid=12123
    try:
        url = r"https://unionapi.vaehub.com/index/receive/save?cid=12123&cde=200&cty=json&ret={%22code%22:200,%22data%22:{%22test%221234567}}"
        resp = HttpMdtHelper.post(url, payload)
    except ModuleNotFoundError as e:
        print("模块未找到异常:", e)
        exit()
    except Exception as e:
        print("请求异常:", e)
        exit()
    print(resp)
    