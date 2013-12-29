# -*- coding: utf-8 -*-
'''The Serializer class, including its metaclass and options (class Meta).'''
from __future__ import absolute_import
import datetime as dt
import json
import copy
import uuid
import types
import warnings

from marshmallow import base, fields, utils
from marshmallow.compat import (with_metaclass, iteritems, text_type,
                                binary_type, OrderedDict)


class SerializerMeta(type):
    '''Metaclass for the Serializer class. Binds the declared fields to
    a ``_declared_fields`` attribute, which is a dictionary mapping attribute
    names to field objects.
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
        self.additional = getattr(meta, 'additional', ())
        if self.fields and self.additional:
            raise ValueError("Cannot set both `fields` and `additional` options"
                            " for the same serializer.")
        self.exclude = getattr(meta, 'exclude', ())
        self.strict = getattr(meta, 'strict', False)
        self.dateformat = getattr(meta, 'dateformat', None)


class BaseSerializer(base.SerializerABC):
    '''Base serializer class with which to define custom serializers.

    Example usage:

    .. code-block:: python

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
        #                ('date_born', 'Sat, 09 Nov 2013 00:10:29 -0000')])

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
    :param bool many: Should be set to ``True`` if ``obj`` is a collection
        so that the object will be serialized to a list.
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
        uuid.UUID: fields.UUID,
        dt.time: fields.Time,
        dt.date: fields.Date,
        dt.timedelta: fields.TimeDelta,
    }

    class Meta(object):
        '''Options object for a Serializer.

        Example usage: ::

            class Meta:
                fields = ("id", "email", "date_created")
                exclude = ("password", "secret_attribute")

        Available options:

        - ``fields``: Tuple or list of fields to include in the serialized result.
        - ``additional``: Tuple or list of fields to include *in addition* to the
            explicitly declared fields. ``additional`` and ``fields`` are
            mutually-exclusive options.
        - ``exclude``: Tuple or list of fields to exclude in the serialized result.
        - ``dateformat``: Date format for all DateTime fields that do not have their
            date format explicitly specified.
        - ``strict``: If ``True``, raise errors during marshalling rather than
            storing them.
        '''
        pass

    def __init__(self, obj=None, extra=None, only=None,
                exclude=None, prefix='', strict=False, many=False):
        if not many and utils.is_collection(obj):
            warnings.warn('Implicit collection handling is deprecated. Set '
                            'many=True to serialize a collection.',
                            category=DeprecationWarning)
        self.many = many
        self.opts = SerializerOpts(self.Meta)
        if isinstance(obj, types.GeneratorType):
            self.obj = list(obj)
        else:
            self.obj = obj
        self.only = only or ()
        self.exclude = exclude or ()
        self.prefix = prefix
        self.fields = self.__get_fields()  # Dict of fields
        if strict or self.opts.strict:
            self.strict = True
        else:
            self.strict = False
        #: Callable marshalling object
        self._marshal = fields.Marshaller(prefix=self.prefix, strict=self.strict)
        # Store the marshalled data
        # MUST occur upon initialization
        self._data = self.marshal(self.obj, self.fields, many=self.many)
        if extra:
            self._data.update(extra)

    def __get_fields(self):
        '''Return the declared fields for the object as an OrderedDict.'''
        ret = OrderedDict()
        declared_fields = copy.deepcopy(self._declared_fields)  # Copy _declared_fields
                                                                # from metaclass
        # Explicitly declared fields
        for field_name, field_obj in iteritems(declared_fields):
            ret[field_name] = field_obj

        if self.opts.fields:
            # Return only fields specified in fields option
            ret = self.__get_opts_fields(ret, self.opts.fields)
        elif self.opts.additional:
            # Return declared fields + additional fields
            field_names = tuple(ret.keys()) + tuple(self.opts.additional)
            ret = self.__get_opts_fields(ret, field_names)

        # if only __init__ param is specified, only return those fields
        if self.only:
            filtered = OrderedDict()
            for field_name in self.only:
                if field_name not in ret:
                    raise AttributeError(
                        '"{0}" is not a valid field for {1}.'
                            .format(field_name, self.obj))
                filtered[field_name] = ret[field_name]
            self.__initialize_fields(filtered)
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
        self.__initialize_fields(ret)
        return ret

    def __initialize_fields(self, fields_dict):
        '''Set the parents of all field objects in fields_dict to self, and
        set the dateformat specified in ``class Meta``, if necessary.
        '''
        for field_name, field_obj in iteritems(fields_dict):
            if not field_obj.parent:
                field_obj.parent = self
            if not field_obj.name:
                field_obj.name = field_name
            if isinstance(field_obj, fields.DateTime):
                if field_obj.dateformat is None:
                    field_obj.dateformat = self.opts.dateformat
        return fields_dict

    def __get_opts_fields(self, declared_fields, field_names):
        '''Return only those field_name:field_obj pairs specified by
        ``field_names``.

        :param dict declared_fields: The original dictionary of explicitly
            declared fields.
        :param tuple field_names: List of field names to include in the final
            return dictionary.
        '''
        # Convert obj to a dict
        if not isinstance(self.opts.fields, (list, tuple)):
            raise ValueError("`fields` option must be a list or tuple.")
        obj_marshallable = utils.to_marshallable_type(self.obj)
        if self.many:
            try:  # Homogeneous collection
                obj_dict = utils.to_marshallable_type(obj_marshallable[0])
            except IndexError:  # Nothing to serialize
                return declared_fields
        else:
            obj_dict = obj_marshallable
        ret = OrderedDict()
        for key in field_names:
            if key in declared_fields:
                ret[key] = declared_fields[key]
            else:
                try:
                    if obj_dict:
                        attribute_type = type(obj_dict[key])
                        field_obj = self.TYPE_MAPPING.get(attribute_type, fields.Raw)()
                    else:  # Object is None
                        field_obj = fields.Raw()
                except KeyError:
                    raise AttributeError(
                        '"{0}" is not a valid field for {1}.'.format(key, self.obj))
                # map key -> field (default to Raw)
                ret[key] = field_obj
        return ret

    def marshal(self, data, fields_dict, many=False):
        """Takes the data (a dict, list, or object) and a dict of fields.
        Stores any errors that occur.

        :param data: The actual object(s) from which the fields are taken from
        :param dict fields_dict: A dict whose keys will make up the final serialized
                       response output
        """
        return self._marshal(data, fields_dict, many=many)

    @property
    def data(self):
        '''The serialized data as an ``OrderedDict``.
        '''
        return self._data

    @property
    def json(self):
        '''The data as a JSON string.'''
        return self.to_json()

    @property
    def errors(self):
        '''Dictionary of errors raised during serialization.'''
        return self._marshal.errors

    def to_json(self, *args, **kwargs):
        '''Return the JSON representation of the data. Takes the same arguments
        as Pythons built-in ``json.dumps``.
        '''
        ret = json.dumps(self.data, *args, **kwargs)
        # On Python 2, json.dumps returns bytestrings
        # On Python 3, json.dumps returns unicode
        # Ensure that a bytestring is returned
        if isinstance(ret, text_type):
            return binary_type(ret.encode('utf-8'))
        return ret

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
    __doc__ = BaseSerializer.__doc__
