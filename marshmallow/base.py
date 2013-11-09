# -*- coding: utf-8 -*-


class Field(object):
    '''Abstract base class from which all Field classes inherit.
    '''
    parent = None

    def format(self, value):
        raise NotImplementedError

    def output(self, value):
        raise NotImplementedError

    def __repr__(self):
        return "<{0} Field>".format(self.__class__.__name__)

    __str__ = __repr__
