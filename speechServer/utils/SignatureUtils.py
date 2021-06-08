# -*- coding: utf-8 -*-
# @Time  : 2021/5/27 13:29
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : SignatureUtils.py

def check_signature(args: dict) -> bool:
    """
    check the signature of args of websockets
    对 websockt连接中的参数鉴权
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

        return True
