# -*- coding: utf-8 -*-
# @Time  : 2021/5/31 9:06
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : redis_push.py
import json

import redis

# 默认不在列表里的都往google送
from speechServer.pojo.TranscriptBody import TranscriptBody

languages_code = {
    "zh": {
        "engine": "ifly",
        "language": "简体中文"
    }

}
# todo 改了  GOOGLE_AUDIO_CHANNEL
# --- CHANNEL --
GOOGLE_CONNECT_CHANNEL = "google_connect"
GOOGLE_DISCONNECT_CHANNEL = "google_disconnect"
GOOGLE_ASR_RESULT_CHANNEL = "google_result"
GOOGLE_AUDIO_CHANNEL = "google"

# --- CHANNEL --
IFLY_CONNECT_CHANNEL = "ifly_connect"
IFLY_DISCONNECT_CHANNEL = "ifly_disconnect"
IFLY_ASR_RESULT_CHANNEL = "ifly_result"
IFLY_AUDIO_CHANNEL = "ifly"

ALL_CHANNELS = {
    "google": {
        "result": GOOGLE_ASR_RESULT_CHANNEL,
        "audio": GOOGLE_AUDIO_CHANNEL
    },
    "ifly": {
        "result": IFLY_ASR_RESULT_CHANNEL,
        "audio": IFLY_AUDIO_CHANNEL
    }
}
if __name__ == '__main__':

    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    # add configs
    # r.setnx("languages_code", json.dumps(languages_code))
    # r.setnx("ALL_CHANNELS", json.dumps(ALL_CHANNELS))
    for i in range(2):
        r.publish(IFLY_ASR_RESULT_CHANNEL, TranscriptBody(result=f'hi {i}', task_id=1402442997366398976, speech_id='auto', speech_type='final').json())