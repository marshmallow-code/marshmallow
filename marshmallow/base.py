# -*- coding: utf-8 -*-


class Field(object):
    '''Abstract base class from which all Field classes inherit.
    '''

    def format(self, value):
        raise NotImplementedError

    def output(self, value):
        raise NotImplementedError
