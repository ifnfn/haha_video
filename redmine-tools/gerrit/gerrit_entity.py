import functools
import time

from datetime import datetime

from simplemodel import SimpleModel, Self
from simplemodel.fields import DictField


def build_keyed_dict(key_attr, value_type, dct):
    result = {}
    for key in dct:
        value = value_type(dct[key])
        setattr(value, key_attr, key)
        result[key] = value
    return result
        

def keyed_dict(key_field, value_type):
    return functools.partial(build_keyed_dict, key_field, value_type)


class GerritEntity(SimpleModel):
    pass


class Timestamp(datetime):
    def __new__(cls, *args):
        if len(args) == 1:
            obj = args[0] 
            if isinstance(obj, datetime):
                args = obj.utctimetuple()[:6] + [obj.microsecond]
            elif isinstance(obj, basestring):
                return Timestamp.strptime(obj[:26], '%Y-%m-%d %H:%M:%S.%f')
        return super(Timestamp, cls).__new__(cls, *args)