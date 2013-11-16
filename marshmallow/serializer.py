# -*- coding: utf-8 -*-
'''The Serializer class, including its metaclass and options (class Meta).'''
from __future__ import absolute_import, print_function
import datetime as dt
import json
import copy

from marshmallow import base, exceptions, fields, utils
from marshmallow.compat import (with_metaclass, iteritems, text_type,
                                binary_type, OrderedDict)


class SerializerMeta(type):
    '''Metaclass for the Serializer class. Binds the declared fields to
    a ``_declared_fields`` attribute, which is a dictionary mapping attribute
    names to field classes and instances.
    '''

    def __new__(mcs, name, bases, attrs):
        attrs['_declared_fields'] = mcs.get_declared_fields(bases, attrs, base.FieldABC)
        return super(SerializerMeta, mcs).__new__(mcs, name, bases, attrs)

    @classmethod
    def get_declared_fields(mcs, bases, attrs, field_class):
        '''Return the declared fields of a class as an OrderedDict.

        :param tuple bases: Tuple of classes the class is subclassing.
        :param dict attrs: Dictionary of class attributes.
        :param type field_class: The base field class. Any class attribute that
            is of this type will be be returned
        '''
        declared = [(field_name, attrs.pop(field_name))
                    for field_name, val in list(iteritems(attrs))
                    if utils.is_instance_or_subclass(val, field_class)]
        # If subclassing another Serializer, inherit its fields
        # Loop in reverse to maintain the correct field order
        for base_class in bases[::-1]:
            if hasattr(base_class, '_declared_fields'):
                declared = list(base_class._declared_fields.items()) + declared
        return OrderedDict(declared)


class SerializerOpts(object):
    """class Meta options for the Serializer. Defines defaults."""

    def __init__(self, meta):
        self.fields = getattr(meta, 'fields', ())
        self.exclude = getattr(meta, 'exclude', ())
        self.strict = getattr(meta, 'strict', False)


class BaseSerializer(base.SerializerABC):
    '''Base serializer class which defines the interface for a serializer.
    '''
    TYPE_MAPPING = {
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
                strict = False
        '''
        pass

    def __init__(self, obj=None, extra=None, only=None,
                exclude=None, prefix='', strict=False):
        self.opts = SerializerOpts(self.Meta)
        self.obj = obj
        self.only = only or ()
        self.exclude = exclude or ()
        self.prefix = prefix
        self.fields = self.__get_fields()  # Dict of fields
        self.errors = {}
        self.strict = strict
        #: The serialized data as an ``OrderedDict``
        self.data = self.to_data()
        if extra:
            self.data.update(extra)

    def __get_fields(self):
        '''Return the declared fields for the object as an OrderedDict.'''
        ret = OrderedDict()
        declared_fields = copy.deepcopy(self._declared_fields)  # Copy _declared_fields
                                                                # from metaclass
        # Explicitly declared fields
        for field_name, field_obj in iteritems(declared_fields):
            ret[field_name] = field_obj

        # If "fields" option is specified, use those fields
        if self.opts.fields:
            ret = self.__get_opts_fields(ret)

        # if only __init__ param is specified, only return those fields
        if self.only:
            filtered = OrderedDict()
            for field_name in self.only:
                if field_name not in ret:
                    raise AttributeError(
                        '"{0}" is not a valid field for {1}.'
                            .format(field_name, self.obj))
                filtered[field_name] = ret[field_name]
            self.__set_parents(filtered)
            return filtered

        # If "exclude" option or param is specified, remove those fields
        if not isinstance(self.opts.exclude, (list, tuple)) or \
                            not isinstance(self.exclude, (list, tuple)):
            raise ValueError("`exclude` must be a list or tuple.")
        excludes = set(self.opts.exclude + self.exclude)
        if excludes:
            for field_name in excludes:
                ret.pop(field_name, None)
        # Set parents
        self.__set_parents(ret)
        return ret

    def __set_parents(self, fields_dict):
        '''Set the parents of all field objects in fields_dict to self.'''
        for _, field_obj in iteritems(fields_dict):
            if not field_obj.parent:
                field_obj.parent = self
        return fields_dict

    def __get_opts_fields(self, declared_fields):
        '''Return only those field_name:field_obj pairs specified in the fields
        option of class Meta.
        '''
        # Convert obj to a dict
        if not isinstance(self.opts.fields, (list, tuple)):
            raise ValueError("`fields` option must be a list or tuple.")
        obj_marshallable = utils.to_marshallable_type(self.obj)
        if isinstance(obj_marshallable, (list, tuple)):  # Homogeneous list
            if len(obj_marshallable) > 0:
                obj_dict = utils.to_marshallable_type(obj_marshallable[0])
            else:  # Nothing to serialize
                return declared_fields
        else:
            obj_dict = obj_marshallable
        new = OrderedDict()
        for key in self.opts.fields:
            if key in declared_fields:
                new[key] = declared_fields[key]
            else:
                try:
                    attribute_type = type(obj_dict[key])
                except KeyError:
                    raise AttributeError(
                        '"{0}" is not a valid field for {1}.'.format(key, self.obj))
                # map key -> field (default to Raw)
                new[key] = self.TYPE_MAPPING.get(attribute_type, fields.Raw)()
        return new


    @property
    def json(self):
        '''The data as a JSON string.'''
        return self.to_json()

    def marshal(self, data, fields_dict):
        """Takes the data (a dict, list, or object) and a dict of fields.
        Stores any errors that occur.

        :param data: The actual object(s) from which the fields are taken from
        :param dict fields_dict: A dict whose keys will make up the final serialized
                       response output
        """
        if utils.is_collection(data):
            return [self.marshal(d, fields_dict) for d in data]
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
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
                if self.strict or self.opts.strict:
                    raise err
                self.errors[key] = text_type(err)
                item = (key, None)
            items.append(item)
        return OrderedDict(items)

    def to_data(self, *args, **kwargs):
        return self.marshal(self.obj, self.fields, *args, **kwargs)

    def to_json(self, *args, **kwargs):
        return json.dumps(self.data, *args, **kwargs)

    def is_valid(self, field_names=None):
        """Return ``True`` if all data are valid, ``False`` otherwise.

        :param field_names: List of field names (strings) to validate.
            If ``None``, all fields will be validated.
        """
        if field_names is not None and type(field_names) not in (list, tuple):
            raise ValueError("field_names param must be a list or tuple")
        fields_to_validate = field_names or self.fields.keys()
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
        # OrderedDict([('name', u'Guido van Rossum'),
                        ('date_born', 'Sat, 09 Nov 2013 00:10:29 -0000')])

    :param obj: The object or collection of objects to be serialized.
    :param dict extra: A dict of extra attributes to bind to the serialized result.
    :param tuple only: A list or tuple of fields to serialize. If ``None``, all
        fields will be serialized.
    :param tuple exclude: A list or tuple of fields to exclude from the
        serialized result.
    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    :param bool strict: If ``True``, raise errors if invalid data are passed in
        instead of failing silently and storing the errors.
    '''
    pass
