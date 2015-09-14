# -*- coding: utf-8 -*-
import sys
import itertools

PY2 = int(sys.version[0]) == 2
PY26 = PY2 and int(sys.version_info[1]) < 7

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
    zip_longest = itertools.izip_longest
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
    iterkeys = lambda d: d.keys()
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()
    zip_longest = itertools.zip_longest
    from collections import OrderedDict
    OrderedDict = OrderedDict

def plain_function(f):
    """Ensure that ``callable`` is a plain function rather than an unbound method, as
    may happen in Python 2 when setting functions as class variables. This is particularly
    useful for class Meta options that are functions. ::

        class MySchemaOpts(SchemaOpts):
            def __init__(self, meta):
                self.some_option = plain_function(getattr(meta, 'some_option', None))

        class MySchema(Schema):
            OPTIONS_CLASS = MySchemaOpts

            class Meta:
                some_option = my_function

    Returns `None` if callable is `None`.
    """
    if PY2 and f:
        return f.im_func
    # Python 3 doesn't have bound/unbound methods, so don't need to do anything
    return f

# From six
def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):  # noqa

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})
