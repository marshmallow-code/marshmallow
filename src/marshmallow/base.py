# -*- coding: utf-8 -*-
"""Abstract base classes.

These are necessary to avoid circular imports between core.py and fields.py.
"""
import copy


class FieldABC(object):
    """Abstract base class from which all Field classes inherit.
    """
    parent = None
    name = None

    def serialize(self, attr, obj, accessor=None):
        raise NotImplementedError

    def deserialize(self, value):
        raise NotImplementedError

    def _serialize(self, value, attr, obj):
        raise NotImplementedError

    def _deserialize(self, value, attr, ob):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        ret = copy.copy(self)
        return ret


class SchemaABC(object):
    """Abstract base class from which all Schemas inherit."""

    def dump(self, obj):
        raise NotImplementedError

    def dumps(self, obj, *args, **kwargs):
        raise NotImplementedError

    def load(self, data):
        raise NotImplementedError

    def loads(self, data):
        raise NotImplementedError
