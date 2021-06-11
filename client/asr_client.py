# -*- coding: utf-8 -*-
# @Time  : 2021/6/10 11:56
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : asr_client.py
import asyncio
import base64
import json
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


async def send_file(filepath: str):
    with open(filepath, 'rb') as file:
        uri = "ws://localhost:8000/v1/asr?date=1&appkey=2&signature=3"
        async with websockets.connect(uri) as websocket:
            asyncio.create_task(recv(websocket))
            count = 0
            finished = 0
            while True:
                chunk = file.read(1280)
                data = base64.b64encode(chunk).decode()

                if not chunk:
                    status = 'end'
                    if finished == 0:
                        await websocket.send(AudioBody(
                            language_code='zh',
                            audio_format='wav/16000',
                            status=status,
                            data=data).json())

                        finished = 1
                    # 等待关闭连接
                    await asyncio.sleep(3)
                    continue

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
            while not websocket.closed:
                await asyncio.sleep(2)


async def recv(ws):
    try:
        while not ws.closed:
            result = await ws.recv()
            print(result)
            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosedOK:
        print("websocket connection closed, task finished")
    except ConnectionResetError:
        print('server is not available')


if __name__ == '__main__':
    asyncio.run(send_file("test_1.pcm"))