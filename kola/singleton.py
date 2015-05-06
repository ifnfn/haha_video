#! /usr/bin/python3
# -*- coding: utf-8 -*-

class SingletonType(type):
    def __call__(cls):
        if getattr(cls, '__instance__', None) is None:
            instance = cls.__new__(cls)
            instance.__init__()
            cls.__instance__ = instance
        return cls.__instance__

# Usage
class Singleton(object,metaclass=SingletonType):
    def __init__(self):
        print('__init__:', self)
