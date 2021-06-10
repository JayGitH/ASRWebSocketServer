# -*- coding: utf-8 -*-
# @Time  : 2021/6/9 10:57
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : AudioBody.py
import json


class AudioBody:
    def __init__(self, language_code: str, audio_format: str, status: str, data: str, task_id: int):
        """
        the body of audio information and binary data
        Args:
            language_code (str): the language_code .like `zh`
            audio_format (str): file type and bit rate. like `wav/16000`
            status (str): [`start`, `end`]
            data (str): binary data
        """
        self.language_code = language_code
        self.audio_format = audio_format
        self.status = status
        self.data = data
        self.task_id = task_id

    def __dict__(self):
        return {
            "language_code": self.language_code,
            "audio_format": self.audio_format,
            "status": self.status,
            "data": self.data,
            "task_id": self.task_id
        }

    def json(self):
        return json.dumps(self.__dict__())
