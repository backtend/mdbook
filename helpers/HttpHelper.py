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

class HttpHelper:
    APP_TAG = "default"
    APP_KEY = "appkeyiiiiii"
    APP_SECRET = "bccfa723e09f9f46d3b6d1e6e8d293cb"
    BASE_URL = "https://unapi.juhuibu.com"

    @staticmethod
    def _get_nonce(length=16):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def _get_client_key():
        mac = uuid.getnode()
        sys_info = platform.platform()
        raw = f"{mac}-{sys_info}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_auth_header():
        timestamp = str(int(time.time()))
        nonce = HttpHelper._get_nonce()
        sign_raw = f"{HttpHelper.APP_KEY}{timestamp}{nonce}{HttpHelper.APP_SECRET}"
        signature = hashlib.sha256(sign_raw.encode("utf-8")).hexdigest()

        token_raw = f"{HttpHelper.APP_TAG}:{timestamp}:{HttpHelper.APP_KEY}:{nonce}:{signature}"
        token_base64 = base64.b64encode(token_raw.encode("utf-8")).decode("utf-8")

        return f"Bearer {token_base64}"

    # @staticmethod
    # def post(url, data):
    #     headers = {
    #         "Authorization": HttpHelper._build_auth_header(),
    #         "Accept": "application/json",
    #         "CLIENT-KEY": HttpHelper._get_client_key(),
    #         "Content-Type": "application/json"
    #     }
    #     url = url if url.startswith("http") else f"{HttpHelper.BASE_URL}{url.lstrip('.')}"
    #     try:
    #         response = requests.post(url, headers=headers, json=data, timeout=10, verify=True)
    #     except requests.RequestException as e:
    #         return {"code":500,"msg": str(e)}

    #     if response.status_code != 200:
    #         return {"code":500,"msg": f"请求失败，状态码: {response.status_code}, 原因: {response.text}"}

    #     response.raise_for_status()
        
    #     try:
    #         return response.json().get("data", {"code": 500, "msg": "响应数据格式错误"})
    #     except json.JSONDecodeError:
    #         return {"code":500,"msg": "非JSON响应", "response_text": response.text}


    @staticmethod
    def post(url, data, extra_headers=None):
        """
        发送POST请求，支持自定义headers，支持文件/文件数组上传。
        :param url: 请求URL（可相对或绝对）
        :param data: 请求体，可以包含普通字段，也可以包含文件对象或文件列表
        :param extra_headers: 额外的header（会覆盖默认header）
        :return: dict 响应结果
        """
        headers = {
            "Authorization": HttpHelper._build_auth_header(),
            "Accept": "application/json",
            "CLIENT-KEY": HttpHelper._get_client_key(),
            "Content-Type": "application/json"
        }
        # 合并用户传入的 headers
        if extra_headers:
            headers.update(extra_headers)
        
        payload = data.copy()

        # 判断是否有文件
        files = None
        if "upload_file" in payload:
            files = {"upload_file": payload.pop("upload_file")}
            headers.pop("Content-Type", None)  # requests 会自动处理 multipart
        elif "upload_files" in payload:
            files = [("upload_files[]", f) for f in payload.pop("upload_files")]
            headers.pop("Content-Type", None)
        print(files)  # 调试输出 files 内容

        url = url if url.startswith("http") else f"{HttpHelper.BASE_URL}{url.lstrip('.')}"
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload if not files else None,
                data=payload if files else None,
                files=files,
                timeout=15,
                verify=True
            )
        except requests.RequestException as e:
            raise Exception(f"HTTP请求失败: {e}")

        if response.status_code != 200:
            raise Exception(f"请求失败，状态码: {response.status_code}, 原因: {response.text}")

        response.raise_for_status()
        print(response.text)  # 调试输出完整响应文本
        try:
            data = response.json().get("data", {"code": 500, "msg": "响应数据格式错误"})
        except json.JSONDecodeError:
            raise Exception(f"非JSON响应: {response.text}")

        return data

    # @staticmethod
    # def file(url, file, extra_fields=None):
    #     """
    #     上传单个或多个文件
    #     :param url: 接口路径
    #     :param file_paths: 单个文件路径(str) 或 多个文件路径(list)
    #     :param extra_fields: 附加表单字段（可选）
    #     """
    #     headers = {
    #         "Authorization": HttpHelper._build_auth_header(),
    #         "Accept": "application/json",
    #         "CLIENT-KEY": HttpHelper._get_client_key(),
    #     }

    #     # 转换 file_paths 参数
    #     files = []
    #     if isinstance(file, str):
    #         # 单文件
    #         if not os.path.exists(file):
    #             return {"code": 400, "msg": f"文件不存在: {file}"}
    #         files = {
    #             "file": (os.path.basename(file), open(file, "rb"))
    #         }
    #     elif isinstance(file, list):
    #         # 多文件
    #         if len(file) == 0:
    #             return {"code": 400, "msg": "文件列表不能为空"}
    #         file_items = []
    #         for f in file:
    #             if not os.path.exists(f):
    #                 return {"code": 400, "msg": f"文件不存在: {f}"}
    #             file_items.append(("files", (os.path.basename(f), open(f, "rb"))))
    #         files = file_items
    #     else:
    #         return {"code": 400, "msg": "file 参数必须是 str 或 list"}

    #     data = extra_fields if extra_fields else {}
    #     url = HttpHelper._build_url(url)

    #     try:
    #         response = requests.post(url, headers=headers, files=files, data=data, timeout=30, verify=True)
    #     except requests.RequestException as e:
    #         return {"code": 500, "msg": str(e)}

    #     if response.status_code != 200:
    #         return {"code": 500, "msg": f"上传失败，状态码: {response.status_code}, 原因: {response.text}"}

    #     try:
    #         return response.json()
    #     except json.JSONDecodeError:
    #         return {"code": 500, "msg": "非JSON响应", "response_text": response.text}



if __name__ == "__main__":
    # 示例参数，可根据实际接口要求修改
    payload = {"aaa": "bbb", "ccc": 123}
    # result = HttpHelper.post("/robotads/task", payload)
    # print(json.dumps(result, ensure_ascii=False, indent=2))

    # # 1️⃣ 普通 JSON 请求
    # # HttpHelper.post("/api/path", {"key": "value"})

    # # 2️⃣ 上传单个文件
    # HttpHelper.file("/upload/single", "test.png", {"userId": 1001})

    # # 3️⃣ 上传多个文件
    # HttpHelper.file("/upload/multi", ["a.jpg", "b.jpg"], {"group": "ads"})



    # # 兼容性的post使用方式：

    # # 普通 JSON 请求：
    # resp = HttpHelper.post("/user/login", {"username": "test", "password": "123456"})
    
    # # 单文件上传：
    with open("crack.png", "rb") as f:
        resp = HttpHelper.post("/home/uploadapi/fileup", {
            "upload_file": f,
            "description": "头像"
        })
        print(resp)

    # 多文件上传：
    # files = [open("crack.png", "rb"), open("logo.webp", "rb")]
    # result = HttpHelper.post("/home/uploadapi/fileups", {
    #     "upload_files": files,
    #     "userId": 123
    # })
    # print(result)

    # print(json.dumps(result, ensure_ascii=False, indent=2))
