# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import datetime as dt
import json
import copy

from marshmallow import base, exceptions, fields, utils
from marshmallow.compat import (with_metaclass, iteritems, text_type,
                                binary_type, OrderedDict)


def _get_declared_fields(bases, attrs, field_class):
    '''Return the declared fields of a class as an OrderedDict.'''
    declared = [(field_name, attrs.pop(field_name))
                for field_name, val in list(iteritems(attrs))
                if utils.is_instance_or_subclass(val, field_class)]
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
        attrs['_base_fields'] = _get_declared_fields(bases, attrs, base.FieldABC)
        return super(SerializerMeta, cls).__new__(cls, name, bases, attrs)


class SerializerOpts(object):
    """class Meta options for the Serializer. Defines default options."""

    def __init__(self, meta):
        self.fields = getattr(meta, 'fields', ())
        self.exclude = getattr(meta, 'exclude', ())


class BaseSerializer(base.SerializerABC):
    '''Base serializer class which defines the interface for a serializer.
    '''
    type_mapping = {
        text_type: fields.String,
        binary_type: fields.String,
        dt.datetime: fields.DateTime,
        float: fields.Float,
        bool: fields.Boolean,
        tuple: fields.Raw,
        list: fields.Raw,
        set: fields.Raw,
        int: fields.Integer,
    }

    class Meta(object):
        '''Options object for a Serializer.

        Example usage: ::

            class Meta:
                fields = ("id", "email", "date_created")
                exclude = ("password", "secret_attribute")
        '''
        pass

    def __init__(self, obj=None, extra=None, prefix=''):
        self.opts = SerializerOpts(self.Meta)
        self.obj = obj
        self.prefix = prefix
        self.fields = self.__get_fields()  # Dict of fields
        self.errors = {}
        #: The serialized data as an ``OrderedDict``
        self.data = self.to_data()
        if extra:
            self.data.update(extra)

    def __get_fields(self):
        '''Return the declared fields for the object as an OrderedDict.'''
        ret = OrderedDict()
        base_fields = copy.deepcopy(self._base_fields)  # Copy _base_fields
                                                        # from metaclass
        # Explicitly declared fields
        for field_name, field_obj in iteritems(base_fields):
            ret[field_name] = field_obj

        # If "fields" option is specified, use those fields
        if self.opts.fields:
            # Convert obj to a dict
            if not isinstance(self.opts.fields, (list, tuple)):
                raise ValueError("`fields` option must be a list or tuple.")
            obj_marshallable = utils.to_marshallable_type(self.obj)
            if isinstance(obj_marshallable, (list, tuple)):  # Homogeneous list of objects
                obj_dict = utils.to_marshallable_type(obj_marshallable[0])
            else:
                obj_dict = obj_marshallable
            new = OrderedDict()
            for key in self.opts.fields:
                if key in ret:
                    new[key] = ret[key]
                else:
                    try:
                        attribute_type = type(obj_dict[key])
                    except KeyError:
                        raise AttributeError(
                            '"{0}" is not a valid field for the object.'.format(key))
                    # map key -> field (default to Raw)
                    if self.type_mapping.get(attribute_type) == fields.List:
                        # Iterables are mapped to Raw Lists
                        new[key] = fields.List(fields.Raw)
                    else:
                        new[key] = self.type_mapping.get(attribute_type, fields.Raw)()
            ret = new

        # If "exclude" option is specified, remove those fields
        if self.opts.exclude:
            if not isinstance(self.opts.exclude, (list, tuple)):
                raise ValueError("`exclude` option must be a list or tuple.")
            for field_name in self.opts.exclude:
                ret.pop(field_name, None)

        # Set parents
        for field_name, field_obj in iteritems(ret):
            if not field_obj.parent:
                field_obj.parent = self
        return ret

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
        if utils.is_iterable_but_not_string(data):
            return [self.marshal(d, fields) for d in data]
        items = []
        for attr_name, field_obj in iteritems(fields):
            key = self.prefix + attr_name
            try:
                if isinstance(field_obj, dict):
                    item = (key, self.marshal(data, field_obj))
                else:
                    try:
                        item = (key, field_obj.output(attr_name, data))
                    except TypeError:
                        # field declared as a class, not an instance
                        if issubclass(field_obj, base.FieldABC):
                            msg = ('Field for "{0}" must be declared as a '
                                            "Field instance, not a class. "
                                            'Did you mean "fields.{1}()"?'
                                            .format(attr_name, field_obj.__name__))
                            raise TypeError(msg)
                        raise

            except exceptions.MarshallingError as err:  # Store errors
                self.errors[key] = text_type(err)
                item = (key, None)
            items.append(item)
        return OrderedDict(items)

    def to_data(self, *args, **kwargs):
        return self.marshal(self.obj, self.fields)

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

        # Or, equivalently
        class PersonSerializer2(Serializer):
            class Meta:
                fields = ("name", "date_born")

        person = Person("Guido van Rossum")
        serialized = PersonSerializer(person)
        serialized.data
        # OrderedDict([('name', u'Guido van Rossum'), ('date_born', 'Sat, 09 Nov 2013 00:10:29 -0000')])

    :param obj: The object or list or objects to be serialized.
    :param dict extra: A dict of extra attributes to bind to the serialized result.
    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    '''
    pass
