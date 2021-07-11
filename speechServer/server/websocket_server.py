# -*- coding: utf-8 -*-
# @Time  : 2021/5/25 21:16
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : websocket_server.py
import json
import sanic
from sanic import Sanic, text
import asyncio
from sanic.log import logger
# from websockets.legacy.protocol import WebSocketCommonProtocol
from speechServer.config import *
from speechServer.exception.ParameterException import ParametersException
from speechServer.pojo.AudioBody import AudioBody
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

redis = aioredis.from_url(REDIS_URL, password="xiaoyu")


@app.exception(sanic.exceptions.ServerError)
async def catch_anything(request, exception):
    pass


@app.get("/test")
async def test(request):
    return text("hello\n")


@app.websocket("/asr", version=1)
async def handle(request, ws):
    args = request.args
    session_id = IdWorker().get_id()
    app_key = args.get('appkey', None)



    if app_key is None:
        await ws.close(1000, "Parameters error")

    secret = await redis.get(app_key)

    if secret is None:
        await ws.send(ResponseBody(code=401, message="Unauthorized", task_id=session_id).json())
        await ws.close(1000, "Unauthorized")
    current_language_code = None
    # check_signature 鉴权算法查看文档
    if check_signature(args, request.host, request.path, secret):
        while True:

            # 将客户端注册到系统里面，即加入到client 字典中
            clients[session_id] = ws
            # disconnect if receive nothing in WEBSOCKETS_TIME_OUT seconds
            # 在规定时间未接收到任何消息就主动关闭
            try:
                # handle the receive messages
                # 处理接受到的数据
                message = await asyncio.wait_for(ws.recv(), timeout=WEBSOCKETS_TIME_OUT)

                logger.info(f"{[request.ip]} client-{session_id} send message")

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
                    current_language_code = data.get("language_code", None)
                    language_code_list = json.loads(str(await redis.get("languages_code"), encoding='utf-8'))
                    logger.debug(f"load language list: {language_code_list}")
                    channel = language_code_list.get(current_language_code, {"engine": "google"}).get("engine")

                    await handle_data_from_client(data, ws, session_id)

            except asyncio.TimeoutError:
                # Timeout handle
                # 处理超时
                del clients[session_id]
                await ws.send(ResponseBody(code=408, message="Connection Timeout", task_id=session_id).json())
                #
                if current_language_code:

                    await redis.publish(channel, AudioBody(
                        task_id=session_id,
                        language_code=current_language_code,
                        audio_format="wav/16000",
                        data="",
                        status="end",
                    ).json())

                await ws.close(1000, "TIMEOUT")
                break

            except asyncio.exceptions.CancelledError:
                # closed by client handle
                # 处理被客户端主动关闭连接
                logger.info("client closed the connection")
                del clients[session_id]

                if not ws.closed:
                    await ws.send(ResponseBody(code=403, message="The websocket disconnect", task_id=session_id).json())
                    await ws.close(1000, "The websocket disconnect")
                    if current_language_code:
                        await redis.publish(channel, AudioBody(
                            task_id=session_id,
                            language_code=current_language_code,
                            audio_format="wav/16000",
                            data="",
                            status="end",
                        ).json())
                break

            except json.decoder.JSONDecodeError:
                del clients[session_id]
                print(message)
                await ws.send(ResponseBody(code=403, message="The data must be json format", task_id=session_id).json())
                await ws.close(1000, "the String must be json format")
                break

            except ParametersException as param_exception:
                del clients[session_id]
                await ws.send(ResponseBody(code=403, message=param_exception.__str__(), task_id=session_id).json())
                await ws.close(1000, param_exception.__str__())
                break
    else:
        logger.info(f"{request}")
        await ws.send(ResponseBody(code=401, message="Unauthorized or Timeout", task_id=session_id).json())
        await ws.close(1000, "Unauthorized")


async def handle_data_from_client(data: dict, ws, session_id):
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
    audio_format = data.get("audio_format", None)
    status = data.get("status", None)
    data = data.get("data", None)

    # check every parameters is exist
    # 检查每个参数是否存在
    for param_name in ["language_code", "audio_format", "status", "data"]:
        if locals().get(param_name, None) is None:
            raise ParametersException(f"Parameters '{param_name}' is missing")


    # publish to redis
    # 发送给redis
    language_code_list = json.loads(str(await redis.get("languages_code"), encoding='utf-8'))
    logger.debug(f"load language list: {language_code_list}")
    channel = language_code_list.get(language_code, {"engine": "google"}).get("engine")
    logger.info(f"send data on channel: {channel}")
    await redis.publish(channel, AudioBody(
        task_id=session_id,
        language_code=language_code,
        audio_format=audio_format,
        data=data,
        status=status,
    ).json())

    # # todo maybe some bug here , closed the connection before transcription return
    # # todo here is a temporary solution
    # if data.lower() == "end":
    #     # recognition end.
    #     # to prevent the close before transcription return. so the temporary solution is waiting
    #     await ws.send(ResponseBody(code=200, message="Speech recognition finished", task_id=session_id).json())
    #     await ws.close(200, "Speech recognition finished")
    #     del clients[session_id]


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
                status = output["status"]

                if status in ("final", "start", "partial", "error", "end"):
                    ws_client = clients.get(task_id, None)
                    logger.debug(f"now client is  {task_id}, read to send message")
                    if ws_client is None:
                        logger.debug(f"client list : {clients}")
                        logger.warning(f"sid: {task_id} is not exist")
                        continue
                    if ws_client.closed:
                        logger.info(f"client id: {task_id} closed the connection")
                        del clients[task_id]
                        continue

                    await ws_client.send(ResponseBody(code=200,
                                                      message="SUCCESS" if status != "ERROR" else "ERROR",
                                                      task_id=task_id,
                                                      data=TranscriptBody(task_id=task_id,
                                                                          result=result,
                                                                          status=status,
                                                                          speech_id=speech_id
                                                                          ).__dict__()).json())
                else:
                    logger.warning(f"receive type invalid: {status}")
        await asyncio.sleep(0.01)

    await pubsub.unsubscribe(channel)
    await pubsub.close()
    logger.info(f"This is channel: {channel}, subscribe redis finished")


if __name__ == "__main__":
    app.add_task(deliver_data_from_redis_to_client)
    app.run(host="0.0.0.0", port=8000, workers=4, debug=True)
