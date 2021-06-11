# -*- coding: utf-8 -*-
# @Time  : 2021/5/25 17:36
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : xunfei_asr.py
import asyncio
import hashlib
import hmac
import base64
import json, time, threading
import traceback

import aiohttp
import aioredis
import websockets
from urllib.parse import quote
import logging

from aiohttp import WSMsgType

from speechServer.config import REDIS_URL, app_id, api_key
from speechServer.pojo.AudioBody import AudioBody
from speechServer.pojo.TranscriptBody import TranscriptBody

IFLY_ASR_RESULT_CHANNEL = "ifly_result"
IFLY_AUDIO_CHANNEL = "ifly_audio"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
sh1 = logging.StreamHandler()
fmt1 = logging.Formatter(fmt="%(asctime)s - %(levelname)-9s - %(filename)-8s : %(lineno)s line - %(message)s")
sh1.setFormatter(fmt1)
sh1.setLevel(logging.DEBUG)
logger.addHandler(sh1)
base_url = "ws://rtasr.xfyun.cn/v1/ws"

pd = "edu"

end_tag = "{\"end\": true}"

# 储存客户端
clients = dict()

redis = aioredis.from_url(REDIS_URL)


class XunFeiASR:

    def __init__(self, task_id):
        ts = str(int(time.time()))
        tt = (app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        self.task_id = task_id
        self.ws_connect = aiohttp.ClientSession().ws_connect(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        self.websocket = None

    async def send_audio_body(self, body: AudioBody):
        """

        :param body:
        :return:
        """
        count = 0
        # 重试机制
        while self.websocket and count < 10:
            if not self.websocket.closed:
                logger.debug(f"sending messages , status is :{body.status}")
                if body.status in ("start", "partial", "final"):
                    await self.websocket.send_bytes(base64.b64decode(body.data))
                elif body.status == "end":
                    await self.websocket.send_bytes(bytes(end_tag.encode('utf-8')))
                break
            else:
                logger.warning(f"websocket closed by asr server")
            count += 1
            await asyncio.sleep(0.01)

    async def recv(self):
        try:
            async with self.ws_connect as websocket:
                self.websocket = websocket
                while True:
                    result = await websocket.receive()

                    if result.type == WSMsgType.TEXT:

                        result_dict = json.loads(result.data)
                        logger.debug(f"xunfei receive: {result_dict}")
                        # 解析结果
                        if result_dict["action"] == "started":
                            status = "start"
                        elif result_dict["action"] == "result":
                            status = "partial" if str(json.loads(result_dict["data"])["cn"]["st"]["type"]) == "1" else "final"
                        elif result_dict["action"] == "end":
                            status = "end"
                        else:
                            status = "error"

                        if status in ("start", "partial", "final"):
                            result = "" if len(result_dict["data"]) == 0 else json.loads(result_dict["data"])
                            await redis.publish(IFLY_ASR_RESULT_CHANNEL,
                                                TranscriptBody(
                                                    task_id=self.task_id,
                                                    status=status,
                                                    # generate speech id
                                                    speech_id='auto',
                                                    result=result).json())

                        elif status in ("error", "end"):
                            logger.warning(f"rtasr error: {result}")
                            await redis.publish(IFLY_ASR_RESULT_CHANNEL,
                                                TranscriptBody(
                                                    task_id=self.task_id,
                                                    status=status,
                                                    # generate speech id
                                                    speech_id='auto',
                                                    result=result_dict["desc"]
                                                ).json())
                            await websocket.close()
                            break

                    elif result.type == WSMsgType.closed:

                        print('server closed the connection')
                        break
                    elif result.type == WSMsgType.error:
                        break

        except Exception as e:
            logger.warning(traceback.format_exc())
            logger.warning("receive result end in exception")


async def deliver_data_from_redis_to_asr_engine():
    logger.info(f"This is channel: {IFLY_AUDIO_CHANNEL}, start subscribe redis")
    pubsub = redis.pubsub()
    await pubsub.subscribe(IFLY_AUDIO_CHANNEL)
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                logger.info(f"Redis Message Received: {message}")
                if message["type"] == "message":
                    output = json.loads(message['data'])
                    language_code = output["language_code"]
                    audio_format = output["audio_format"]
                    status = output["status"]
                    data = output["data"]
                    task_id = output["task_id"]

                    if status in ("start", "partial", "end", "final"):
                        if status == "end":
                            await asyncio.sleep(0.04)
                            await clinet.send_audio_body(AudioBody(status=status,
                                                                   data=data,
                                                                   language_code=language_code,
                                                                   audio_format=audio_format,
                                                                   task_id=task_id))
                            continue

                        clinet: XunFeiASR = clients.get(task_id, None)
                        if status == "start":
                            if clinet is None:
                                clients[task_id]: XunFeiASR = XunFeiASR(task_id)
                                clinet = clients[task_id]
                                asyncio.create_task(clients[task_id].recv())



                        logger.debug(f"now client is  {task_id}, read to send message")
                        if clinet is None:
                            logger.debug(f"client list : {clients}")
                            logger.warning(f"sid: {task_id} is not exist")
                            continue
                        else:
                            # send data
                            await clinet.send_audio_body(AudioBody(status=status,
                                                                   data=data,
                                                                   language_code=language_code,
                                                                   audio_format=audio_format,
                                                                   task_id=task_id))
                            await asyncio.sleep(0.04)


                    else:
                        await redis.pubsub(IFLY_ASR_RESULT_CHANNEL,
                                           TranscriptBody(
                                               task_id=task_id,
                                               status="error",
                                               result="status is not correct"
                                           ).json())

        except Exception as e:
            logger.warning(traceback.format_exc())
            print(traceback.format_exc())


if __name__ == '__main__':
    asyncio.run(deliver_data_from_redis_to_asr_engine())
