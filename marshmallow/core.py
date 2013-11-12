# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import json
import copy
from pprint import pprint as py_pprint


from marshmallow import base, exceptions
from marshmallow.compat import with_metaclass, iteritems, text_type, OrderedDict


def is_instance_or_subclass(val, class_):
    try:
        return issubclass(val, class_)
    except TypeError:
        return isinstance(val, class_)


def _get_declared_fields(bases, attrs):
    '''Return the declared fields of a class as an OrderedDict.'''
    declared = [(field_name, attrs.pop(field_name))
                for field_name, val in list(iteritems(attrs))
                if is_instance_or_subclass(val, base.Field)]
    # If subclassing another Serializer, inherit its fields
    # Loop in reverse to maintain the correct field order
    for base_class in bases[::-1]:
        if hasattr(base_class, '_base_fields'):
            declared = list(base_class._base_fields.items()) + declared
    return OrderedDict(declared)


class SerializerMeta(type):
    '''Metaclass for the Serializer class. Binds the declared fields to
    a ``_base_fields`` attribute, which is a dictionary mapping attribute
    names to field classes and instances.
    '''

    def __new__(cls, name, bases, attrs):
        attrs['_base_fields'] = _get_declared_fields(bases, attrs)
        return super(SerializerMeta, cls).__new__(cls, name, bases, attrs)


class BaseSerializer(object):
    '''Base serializer class which defines the interface for a serializer.

    :param data: The object, dict, or list to be serialized.
    :param dict extra: A dict of extra attributes to bind to the serialized result.
    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    '''

    def __init__(self, data=None, extra=None, prefix=''):
        self._data = data
        self.prefix = prefix
        self.fields = self.__get_fields()  # Dict of fields
        self.errors = {}
        #: The serialized data as an ``OrderedDict``
        self.data = self.to_data()
        if extra:
            self.data.update(extra)

    def __get_fields(self):
        '''Return the declared fields for the object as an OrderedDict.'''
        base_fields = copy.deepcopy(self._base_fields)  # Copy _base_fields
                                                        # from metaclass
        for field_name, field_obj in iteritems(base_fields):
            if not field_obj.parent:
                field_obj.parent = self
        return base_fields

    @property
    def json(self):
        '''The data as a JSON string.'''
        return self.to_json()

    def marshal(self, data, fields):
        """Takes the data (a dict, list, or object) and a dict of fields.
        Stores any errors that occur.

        :param data: The actual object(s) from which the fields are taken from
        :param dict fields: A dict whose keys will make up the final serialized
                       response output
        """
        if _is_iterable_but_not_string(data):
            return [self.marshal(d, fields) for d in data]
        items = []
        for k, v in iteritems(fields):
            key = self.prefix + k
            try:
                item = (key, self.marshal(data, v) if isinstance(v, dict)
                                            else v.output(k, data))
            except exceptions.MarshallingException as err:  # Store errors
                self.errors[key] = text_type(err)
                item = (key, None)
            items.append(item)
        return OrderedDict(items)

    def to_data(self, *args, **kwargs):
        return self.marshal(self._data, self.fields)

    def to_json(self, *args, **kwargs):
        return json.dumps(self.data, *args, **kwargs)

    def is_valid(self, fields=None):
        """Return ``True`` if all data are valid, ``False`` otherwise.

        :param fields: List of field names (strings) to validate.
            If ``None``, all fields will be validated.
        """
        if fields is not None and type(fields) not in (list, tuple):
            raise ValueError("fields param must be a list or tuple")
        fields_to_validate = fields or self.fields.keys()
        for fname in fields_to_validate:
            if fname not in self.fields:
                raise KeyError('"{0}" is not a valid field name.'.format(fname))
            if fname in self.errors:
                return False
        return True


class Serializer(with_metaclass(SerializerMeta, BaseSerializer)):
    '''Base serializer class with which to define custom serializers.

    Example usage:
    ::

        from datetime import datetime
        from marshmallow import Serializer, fields

        class Person(object):
            def __init__(self, name):
                self.name = name
                self.date_born = datetime.now()

        class PersonSerializer(Serializer):
            name = fields.String()
            date_born = fields.DateTime()

        person = Person("Guido van Rossum")
        serialized = PersonSerializer(person)
        serialized.data
        # OrderedDict([('name', u'Guido van Rossum'), ('date_born', 'Sat, 09 Nov 2013 00:10:29 -0000')])

    :param data: The object, dict, or list to be serialized.
    '''
    pass


def _is_iterable_but_not_string(obj):
    return hasattr(obj, "__iter__") and not hasattr(obj, "strip")


def marshal(data, fields):
    """Takes raw data (in the form of a dict, list, object) and a dict of
    fields to output and filters the data based on those fields.

    :param data: The actual object(s) from which the fields are taken from
    :param dict fields: A dict whose keys will make up the final serialized
                   response output
    """
    if _is_iterable_but_not_string(data):
        return [marshal(d, fields) for d in data]
    items = ((k, marshal(data, v) if isinstance(v, dict)
                                  else v.output(k, data))
                                  for k, v in fields.items())
    return OrderedDict(items)

def pprint(obj, *args, **kwargs):
    '''Pretty-printing function that can pretty-print OrderedDicts
    like regular dictionaries.
    '''
    if isinstance(obj, OrderedDict):
        print(json.dumps(obj, *args, **kwargs))
    else:
        py_pprint(obj, *args, **kwargs)
