# -*- coding: utf-8 -*-
# @Time  : 2021/5/28 9:43
# @Author : lovemefan
# @Email : lovemefan@outlook.com
# @File : ParameterException.py
class ParametersException(Exception):
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description
