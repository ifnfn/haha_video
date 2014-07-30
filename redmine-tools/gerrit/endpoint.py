import functools
import inspect
try:
    import urllib.parse as urllib
except:
    import urllib


def maybe_quote(str_or_none):
    if str_or_none is None:
        return None
    return urllib.quote(str_or_none)


class EndpointMixin(object):
    _endpoint_parent = None

    @classmethod
    def endpoint_parts(cls):
        parts = []
        
        parent = cls._endpoint_parent
        if parent:
            if isinstance(parent, str):
                parent = getattr(inspect.getmodule(cls), parent)
                cls._endpoint_parent = parent
            names.extend(parent.endpoint_parts())

        part = [cls]
        if hasattr(cls, 'endpoint_name'):
            part.append(cls.endpoint_name)
        else:
            part.append('%ss' % cls.__name__.lower())
        parts.append(part)
            
        return parts

    @classmethod
    def endpoint_path(cls, *args):
        args = list(args)
        optional = object()
        args.append(optional)
        
        path_parts = []
        for part_cls, part_name in cls.endpoint_parts():
            path_parts.append(part_name)
            
            part_arg = args.pop(0)

            if part_arg is optional:
                part_arg = ''
                
            if isinstance(part_arg, part_cls):
                part_arg = part_arg.endpoint_id()
                
            if isinstance(part_arg, int):
                part_arg = str(part_arg)

            if not isinstance(part_arg, (int, basestring)):
                raise TypeError
                    
            path_parts.append(part_arg)
                
        path_parts.extend(args[:-1])
            
        return '/'.join(path_parts)

    def endpoint_id(self):
        return self.id


def endpoint_setup(parent=None, name=None):
    def decorator(cls):
        if parent:
            cls._endpoint_parent = parent
        if name:
            cls.endpoint_name = name
        return cls
    return decorator