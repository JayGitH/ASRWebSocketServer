# -*- coding: utf-8 -*-
# @Time  : 2021/5/27 13:29
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : SignatureUtils.py
import asyncio
import base64
import hashlib
import hmac
import time

from speechServer.config import WEBSOCKETS_SURVIVAL_TIME


def check_signature(args: dict, host: str, path: str, secret: str) -> bool:
    """
    check the signature of args of websockets
    对 websockt连接中的参数鉴权
    :param path:
    :param host:
    :param secret:
    :param args : (tuple)  args of request
    :return: (boolean)
    """


    if len(args) == 0:
        return False
    else:
        date = args.get('date', None)
        app_key = args.get('appkey', None)
        signature = args.get('signature', None)
        if date is None or app_key is None or signature is None:
            return False

        if time.time() - float(date) > WEBSOCKETS_SURVIVAL_TIME:
            print("超时，可能有人抓包")
            return False


        # 拼接字符串
        signature_origin = "host: " + host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "appkey: " + app_key + "\n"
        signature_origin += "GET " + path

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(secret, signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        _signature = base64.b64encode(signature_sha).decode(encoding='utf-8')

        # 防止url中出现加号+ 变成空格的问题
        if _signature.replace('+', '') == signature.replace(' ', ''):
            return True
        else:
            print("授权不通过")
            print(signature_origin)
            print(f"server signature: {_signature}")
            print(f"client signature: {signature}")
            return False


