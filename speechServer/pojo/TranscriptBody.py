#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/5/27 下午7:45
# @Author  : lovemefan
# @File    : TranscriptBody.py
import json

from speechServer.utils.snowflake import IdWorker


class TranscriptBody:
    """The transcript body is the result of speech translation task.
    Using as the return format from speech SDK (service layer) to speechRoute (routes layer)
    """
    def __init__(self, task_id: int = None, result: str = None, status: str = None, speech_id: str = None):
        """initial the Transcript body
        Args:
            speech_id (str): status code, detail see backend/utils/StatusCode.py
            result (str)： list of Sentences corresponding to speech,
            status (str): [final,partial,error,end]
            each sentence conclude text and timestamp information.
        """
        self.__task_id = task_id

        if speech_id == 'auto':
            self.__speech_id = f"yuntrans-{IdWorker().get_id()}"
        else:
            self.__speech_id = speech_id

        self.__result = result
        self.__status = status

    def __dict__(self):
        return {
            "task_id": self.__task_id,
            "speech_id": self.__speech_id,
            "status": self.__status,
            "result": self.__result
        }

    def json(self):
        return json.dumps(self.__dict__())



