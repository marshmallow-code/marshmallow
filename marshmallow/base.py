# -*- coding: utf-8 -*-
'''Abstract base classes.

These are necessary to avoid circular imports between core.py and fields.py.
'''


class FieldABC(object):
    '''Abstract base class from which all Field classes inherit.
    '''
    parent = None

    def format(self, value):
        raise NotImplementedError

    def output(self, key, obj):
        raise NotImplementedError

    def __repr__(self):
        return "<{0} Field>".format(self.__class__.__name__)

    __str__ = __repr__


class SerializerABC(object):
    '''Abstract base class from which all Serializers inherit.'''

    def to_data(self):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError

    def is_valid(self, fields=None):
        raise NotImplementedError
