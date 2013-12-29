# -*- coding: utf-8 -*-
'''Abstract base classes.

These are necessary to avoid circular imports between core.py and fields.py.
'''
import copy


class FieldABC(object):
    '''Abstract base class from which all Field classes inherit.
    '''
    parent = None
    name = None

    def format(self, value):
        raise NotImplementedError

    def output(self, key, obj):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        ret = copy.copy(self)
        return ret

    def __repr__(self):
        return "<{0} Field>".format(self.__class__.__name__)

    __str__ = __repr__


class SerializerABC(object):
    '''Abstract base class from which all Serializers inherit.'''

    @property
    def errors(self):
        raise NotImplementedError

    def is_valid(self, fields=None):
        raise NotImplementedError
