# -*- coding: utf-8 -*-
import sys

PY2 = int(sys.version[0]) == 2
PY26 = PY2 and int(sys.version_info[1]) < 7
LINUX = sys.platform.startswith("linux")

if PY2:
    import urlparse
    urlparse = urlparse
    text_type = unicode
    binary_type = str
    string_types = (str, unicode)
    unicode = unicode
    basestring = basestring
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
    if PY26:
        from .ordereddict import OrderedDict
    else:
        from collections import OrderedDict
    OrderedDict = OrderedDict
else:
    import urllib.parse
    urlparse = urllib.parse
    text_type = str
    binary_type = bytes
    string_types = (str,)
    unicode = str
    basestring = (str, bytes)
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())
    from collections import OrderedDict
    OrderedDict = OrderedDict

def with_metaclass(meta, *bases):
    '''Defines a metaclass.

    Creates a dummy class with a dummy metaclass. When subclassed, the dummy
    metaclass is used, which has a constructor that instantiates a
    new class from the original parent. This ensures that the dummy class and
    dummy metaclass are not in the inheritance tree.

    Credit to Armin Ronacher.
    '''
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__
        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)
    return metaclass('temporary_class', None, {})
