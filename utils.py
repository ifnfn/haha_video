import logging

def autostr(i):
    if type(i) == int:
        return str(i)
    else:
        return i

def autoint(i):
    if type(i) == str:
        return i and int(i) or 0
    else:
        return i

def json_get(sets, key, default):
    if key in sets:
        return sets[key]
    else:
        return default
    
logging.basicConfig()
log = logging.getLogger("crawler")
