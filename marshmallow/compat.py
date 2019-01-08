# -*- coding: utf-8 -*-
# flake8: noqa
import sys
import itertools


PY2 = int(sys.version_info[0]) == 2

if PY2:
    import urlparse
    from collections import Mapping, Iterable, MutableSet

    urlparse = urlparse
    text_type = unicode
    binary_type = str
    unicode = unicode
    basestring = basestring
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
    zip_longest = itertools.izip_longest
else:
    import urllib.parse
    from collections.abc import Mapping, Iterable, MutableSet

    urlparse = urllib.parse
    text_type = str
    binary_type = bytes
    unicode = str
    basestring = (str, bytes)
    iterkeys = lambda d: d.keys()
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()
    zip_longest = itertools.zip_longest

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
