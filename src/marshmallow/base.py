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

    def _serialize(self, value, attr, obj, **kwargs):
        raise NotImplementedError

    def _deserialize(self, value, attr, data, **kwargs):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        ret = copy.copy(self)
        return ret


class SchemaABC(object):
    """Abstract base class from which all Schemas inherit."""

    def dump(self, obj, many=None):
        raise NotImplementedError

    def dumps(self, obj, many=None, *args, **kwargs):
        raise NotImplementedError

    def load(self, data, many=None, partial=None, unknown=None):
        raise NotImplementedError

    def loads(
        self, json_data, many=None, partial=None, unknown=None,
        **kwargs
    ):
        raise NotImplementedError
