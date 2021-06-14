# -*- coding: utf-8 -*-
# @Time  : 2021/6/10 11:56
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : asr_client.py
import asyncio
import base64
import hashlib
import hmac
import json
import time
import traceback

import websockets


class AudioBody:
    def __init__(self, language_code: str, audio_format: str, status: str, data: str):
        """
        the body of audio information and binary data
        Args:
            language_code (str): the language_code .like `zh`
            audio_format (str): file type and bit rate. like `wav/16000`
            status (str): [`start`, `end`]
            data : binary data
        """
        self.language_code = language_code
        self.audio_format = audio_format
        self.status = status
        self.data = data

    def __dict__(self):
        return {
            "language_code": self.language_code,
            "audio_format": self.audio_format,
            "status": self.status,
            "data": self.data,
        }

    def json(self):
        return json.dumps(self.__dict__())


async def send_file(filepath: str, url: str):
    with open(filepath, 'rb') as file:

        async with websockets.connect(url) as websocket:
            asyncio.create_task(recv(websocket))
            count = 0
            status = None
            while True:
                chunk = file.read(1280)
                data = base64.b64encode(chunk).decode()

                if not chunk:
                    break

                if count == 0:
                    status = "start"
                else:
                    status = "partial"

                await websocket.send(AudioBody(
                    language_code='zh',
                    audio_format='wav/16000',
                    status=status,
                    data=data).json())

                count += 1
            # waitting closed by server

            status = 'end'

            await websocket.send(AudioBody(
                language_code='zh',
                audio_format='wav/16000',
                status=status,
                data=data).json())

            # 等待关闭连接
            while not websocket.closed:
                await asyncio.sleep(2)


async def recv(ws):
    try:
        while not ws.closed:
            result = await ws.recv()
            print(json.loads(result))
            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosedOK:
        print("websocket connection closed, task finished")
    except ConnectionResetError:
        print('server is not available')


def create_url(host, app_key: str, secret: str, path):
    timestamp = int(time.time())

    # 拼接字符串
    signature_origin = "host: " + host + "\n"
    signature_origin += "date: " + str(timestamp) + "\n"
    signature_origin += "appkey: " + app_key + "\n"
    signature_origin += "GET " + path

    print(signature_origin)

    # 进行hmac-sha256进行加密
    signature_sha = hmac.new(secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode(encoding='utf-8')

    return f"ws://{host}{path}?date={timestamp}&appkey={app_key}&signature={signature}"

if __name__ == '__main__':
    url = create_url('localhost:8000', 'uopcp9EeuFJgBo66FwYw', '2kCPFNALTgPbi9GIzOTCw1bPkvsjhwI9gsMKoRocKW8=', '/v1/asr')
    print(url)
    asyncio.run(send_file("../wavAndTxt/20210331_1377111840651354113.wav", url))

