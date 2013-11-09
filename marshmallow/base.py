# -*- coding: utf-8 -*-


class Field(object):
    '''Abstract base class from which all Field classes inherit.
    '''
    parent = None

    def format(self, value):
        raise NotImplementedError

    def output(self, value):
        raise NotImplementedError
