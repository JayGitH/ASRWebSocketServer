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

import aioredis
import websockets
from urllib.parse import quote
import logging

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
        self.ws_connect = websockets.connect(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        # self.trecv = threading.Thread(target=self.recv)
        # self.trecv.start()

    async def send_audio_body(self, body: AudioBody):
        """

        :param body:
        :return:
        """
        async with self.ws_connect as websocket:
            if body.status == "start" or "partial":
                await websocket.send(base64.b64decode(body.data))
            else:
                await websocket.send(bytes(end_tag.encode('utf-8')))

    async def recv(self):
        try:
            async with self.ws_connect as websocket:
                while not websocket.closed:
                    result = await websocket.recv()
                    print(result)
                    result_dict = json.loads(result)
                    logger.debug(f"xunfei receive: {result_dict}")
                    # 解析结果
                    if result_dict["action"] == "started":
                        status = "start"
                    elif result_dict["action"] == "result":
                        status = "final" if result_dict["data"]["cn"]["st"]["type"] == 1 else "partial"
                    else:
                        status = "error"

                    await redis.publish(IFLY_ASR_RESULT_CHANNEL,
                                        TranscriptBody(
                                            task_id=self.task_id,
                                            status=status,
                                            # generate speech id
                                            speech_id='auto',
                                            result=json.dumps(result_dict["data"])
                                        ).json())

                    if status == "error":
                        logger.warning("rtasr error: " + result)
                        await redis.publish(IFLY_ASR_RESULT_CHANNEL,
                                            TranscriptBody(
                                                task_id=self.task_id,
                                                status=status,
                                                # generate speech id
                                                speech_id='auto',
                                                result=result_dict["desc"]
                                            ).json())
                        await websocket.close()
                        return

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

                    if status in ("start", "partial", "end"):

                        if status == "start":
                            clients[task_id]: XunFeiASR = XunFeiASR(task_id)
                            task = asyncio.create_task(clients[task_id].recv())
                            await task

                        clinet: XunFeiASR = clients.get(task_id, None)
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

                        if status == "end":
                            clinet = clients.get(task_id, None)
                            if clinet is not None:
                                del clients[task_id]
                    else:
                        await redis.pubsub(IFLY_ASR_RESULT_CHANNEL,
                                           TranscriptBody(
                                               task_id=task_id,
                                               status="error",
                                               result="status is not correct"
                                           ).json())

        except Exception as e:
            logger.warning(traceback.format_exc())


if __name__ == '__main__':
    asyncio.run(deliver_data_from_redis_to_asr_engine())
