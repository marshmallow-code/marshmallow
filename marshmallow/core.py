# -*- coding: utf-8 -*-
import json
from collections import OrderedDict

class Serializer(object):
    '''Base serializer class with which to define custom serializers.

    Must define the ``FIELDS`` class variable, which is a dict mapping
    attributes to field classes that format and return the value for each field.
    '''
    FIELDS = {}

    def __init__(self, data=None):
        self._data = data

    @property
    def data(self):
        return self.to_data()

    @property
    def json(self):
        return self.to_json()

    def to_data(self, *args, **kwargs):
        return marshal(self._data, self.FIELDS)

    def to_json(self, *args, **kwargs):
        return json.dumps(self.data, *args, **kwargs)

    @classmethod
    def marshal(cls, data):
        return marshal(data, cls.FIELDS)

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

    def __unicode__(self):
        return unicode(self.data)


def _is_iterable_but_not_string(obj):
    return hasattr(obj, "__iter__") and not hasattr(obj, "strip")


def marshal(data, fields):
    """Takes raw data (in the form of a dict, list, object) and a dict of
    fields to output and filters the data based on those fields.

    :param fields: a dict of whose keys will make up the final serialized
                   response output
    :param data: the actual object(s) from which the fields are taken from

    """
    def make(cls):
        if isinstance(cls, type):
            return cls()
        return cls
    if _is_iterable_but_not_string(data):
        return [marshal(d, fields) for d in data]

    items = ((k, marshal(data, v) if isinstance(v, dict)
                                  else make(v).output(k, data))
                                  for k, v in fields.items())
    return OrderedDict(items)
