# -*- coding: utf-8 -*-
# @Time  : 2021/5/25 21:16
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : websocket_server.py
import json
import sanic
from sanic import Sanic
import asyncio
from sanic.log import logger
from websockets.legacy.protocol import WebSocketCommonProtocol
from speechServer.config import *
from speechServer.exception.ParameterException import ParametersException
from speechServer.pojo.ResponseBody import ResponseBody
from speechServer.pojo.TranscriptBody import TranscriptBody
from speechServer.utils.SignatureUtils import check_signature
from speechServer.utils.snowflake import IdWorker
import aioredis

app = Sanic("asr_server")
app.config.KEEP_ALIVE_TIMEOUT = 1
app.config.REQUEST_TIMEOUT = 1
app.config.RESPONSE_TIMEOUT = 10
app.config.WEBSOCKET_PING_INTERVAL = 2
app.config.WEBSOCKET_TIMEOUT = 10

# 储存客户端
clients = dict()

redis = aioredis.from_url(REDIS_URL)


@app.exception(sanic.exceptions.ServerError)
async def catch_anything(request, exception):
    pass


@app.websocket("/asr", version=1)
async def handle(request, ws):
    args = request.args
    session_id = IdWorker().get_id()

    # check_signature 鉴权算法查看文档
    if check_signature(args):

        while True:

            # 将客户端注册到系统里面，即加入到client 字典中
            clients[session_id] = ws
            # disconnect if receive nothing in WEBSOCKETS_TIME_OUT seconds
            # 在规定时间未接收到任何消息就主动关闭
            try:
                # handle the receive messages
                # 处理接受到的数据
                message = await asyncio.wait_for(ws.recv(), timeout=WEBSOCKETS_TIME_OUT)

                logger.info(f"client-{session_id} send message: {message}")

                # todo 待加入 帧 ping 支持
                if message.lower() == "ping":
                    # answer if receive the heartbeats
                    # 处理心跳
                    await ws.send('pong')
                    continue
                else:
                    # handle the messages except heartbeats
                    # 处理数据
                    data = json.loads(message)
                    await handle_data_from_client(data, ws, session_id)

            except asyncio.TimeoutError:
                # Timeout handle
                # 处理超时
                del clients[session_id]
                await ws.send(ResponseBody(code=408, message="Connection Timeout", task_id=session_id).json())
                await ws.close(408, "TIMEOUT")
                break

            except asyncio.exceptions.CancelledError:
                # closed by client handle
                # 处理被客户端主动关闭连接
                logger.info("client closed the connection")
                del clients[session_id]

                if not ws.closed:
                    await ws.send(ResponseBody(code=403, message="The websocket disconnect", task_id=session_id).json())
                    await ws.close(403, "The websocket disconnect")
                break

            except json.decoder.JSONDecodeError:
                del clients[session_id]
                await ws.send(ResponseBody(code=403, message="The data must be json format", task_id=session_id).json())
                await ws.close(403, "the String must be json format")
                break

            except ParametersException as param_exception:
                del clients[session_id]
                await ws.send(ResponseBody(code=403, message=param_exception.__str__(), task_id=session_id).json())
                await ws.close(403, param_exception.__str__())
                break
    else:
        logger.info(f"{request}")
        await ws.send(ResponseBody(code=401, message="Unauthorized", task_id=session_id).json())
        await ws.close(401, "Unauthorized")


async def handle_data_from_client(data: dict, ws: WebSocketCommonProtocol, session_id):
    """
    handle the data from client
    处理客户端的数据
    including :
    1): validate the data and deliver data publish to redis from client
    2): receive the results from the corresponding session queue
    验证数据，接受接受数据并发布到redis，从对应的session的队列中取出数据
    :param data: the data of client
    :param ws: the websocket instance to send and receive
    :return:
    :exception:  ParametersException
    """

    # validate data
    language_code = data.get("language_code", None)
    audio_format = data.get("format", None)
    status = data.get("status", None)
    data = data.get("data", None)

    # check every parameters is exist
    # 检查每个参数是否存在
    for param_name in ["language_code", "audio_format", "status", "data"]:
        if locals().get(param_name, None) is None:
            raise ParametersException(f"Parameters '{param_name}' is missing")

    if data.lower() == "eof":
        # recognition end,
        await ws.send(ResponseBody(code=200, message="Speech recognition finished", task_id=session_id).json())
        await ws.close(200, "Speech recognition finished")
        del clients[session_id]

    # publish to redis
    # 发送给redis
    language_code_list = json.loads(str(await redis.get("languages_code"), encoding='utf-8'))
    logger.debug(f"load language list: {language_code_list}")
    channel = language_code_list.get(language_code, {"engine": "google"}).get("engine")
    await redis.publish(channel, TranscriptBody(
        task_id=session_id,
        result=data,
        speech_type=status,
        speech_id='auto'
    ).json())


async def deliver_data_from_redis_to_client():
    """
    deliver data from redis and send data to each client
    从redis得到的数据取出放到对应客户端并发送
    :return:
    """
    # todo 老感觉有bug

    all_channels = None
    while True:
        # logger.debug(f"channel list: {clients}")
        # print(str(threading.enumerate()))
        if len(clients) == 0:
            await asyncio.sleep(0.4)
            continue

        new_all_channels = json.loads(await redis.get("ALL_CHANNELS"))

        # 只有在第一次或者，当redis里面的ALL_CHANNELS 改变的时候才会运行以下代码
        if all_channels != new_all_channels:
            all_channels = new_all_channels

            for key, value in all_channels.items():
                logger.info(f"current channel : {key}")
                app.add_task(send_data_to_client_on_one_channel(value['result']))

        else:
            await asyncio.sleep(5)


async def send_data_to_client_on_one_channel(channel: str):
    """
    if websockets client exist and not closed, sent data to client identified by session id
    :param channel:
    :return:
    """
    logger.info(f"This is channel: {channel}, start subscribe redis")
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message is not None:
            logger.info(f"Redis Message Received: {message}")
            if message["type"] == "message":
                output = json.loads(message['data'])
                speech_id = output["speech_id"]
                task_id = output["task_id"]
                result = output["result"]
                _type = output["type"]

                if _type in ("final"):
                    ws_client = clients.get(task_id, None)
                    logger.debug(f"now client is  {task_id}, read to send message")
                    if ws_client is None:
                        logger.debug(f"client list : {clients}")
                        logger.info(f"sid: {task_id} is not exist")
                        continue
                    if ws_client.closed:
                        logger.info(f"client id: {task_id} is closed")
                        clients.pop(task_id)
                        continue

                    await ws_client.send(ResponseBody(code=200,
                                                      message="SUCCESS",
                                                      task_id=task_id,
                                                      data=TranscriptBody(task_id=task_id,
                                                                          result=result,
                                                                          speech_type=_type,
                                                                          speech_id=speech_id
                                                                          ).json()).json())
        await asyncio.sleep(0.01)

    await pubsub.unsubscribe(channel)
    await pubsub.close()
    logger.info(f"This is channel: {channel}, subscribe redis finished")


if __name__ == "__main__":
    # thrd = threading.Thread(
    #     target=deliver_data_from_redis_to_client,
    #     name="AsyncIO Thread"
    # )
    # thrd.start()
    app.add_task(deliver_data_from_redis_to_client)
    app.run(host="0.0.0.0", port=8000, debug=True)