# -*- coding: utf-8 -*-
"""The Serializer class, including its metaclass and options (class Meta)."""
from __future__ import absolute_import
import datetime as dt
import json
import copy
import uuid
import types
import warnings
import functools

from marshmallow import base, fields, utils, class_registry
from marshmallow.compat import (with_metaclass, iteritems, text_type,
                                binary_type, OrderedDict)


class SerializerMeta(type):
    """Metaclass for the Serializer class. Binds the declared fields to
    a ``_declared_fields`` attribute, which is a dictionary mapping attribute
    names to field objects.
    """

    def __new__(mcs, name, bases, attrs):
        attrs['_declared_fields'] = mcs.get_declared_fields(bases, attrs, base.FieldABC)
        new_class = super(SerializerMeta, mcs).__new__(mcs, name, bases, attrs)
        class_registry.register(name, new_class)
        return new_class

    @classmethod
    def get_declared_fields(mcs, bases, attrs, field_class):
        """Return the declared fields of a class as an OrderedDict.

        :param tuple bases: Tuple of classes the class is subclassing.
        :param dict attrs: Dictionary of class attributes.
        :param type field_class: The base field class. Any class attribute that
            is of this type will be be returned
        """
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
        if not isinstance(self.fields, (list, tuple)):
            raise ValueError("`fields` option must be a list or tuple.")
        self.additional = getattr(meta, 'additional', ())
        if not isinstance(self.additional, (list, tuple)):
            raise ValueError("`additional` option must be a list or tuple.")
        if self.fields and self.additional:
            raise ValueError("Cannot set both `fields` and `additional` options"
                            " for the same serializer.")
        self.exclude = getattr(meta, 'exclude', ())
        if not isinstance(self.exclude, (list, tuple)):
            raise ValueError("`exclude` must be a list or tuple.")
        self.strict = getattr(meta, 'strict', False)
        self.dateformat = getattr(meta, 'dateformat', None)
        self.json_module = getattr(meta, 'json_module', json)


class BaseSerializer(base.SerializerABC):
    """Base serializer class with which to define custom serializers.

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
    """
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

    OPTIONS_CLASS = SerializerOpts

    class Meta(object):
        """Options object for a Serializer.

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
        - ``json_module``: JSON module to use. Defaults to the ``json`` module
            in the stdlib.
        """
        pass

    def __init__(self, obj=None, extra=None, only=None,
                exclude=None, prefix='', strict=False, many=False,
                context=None):
        if not many and utils.is_collection(obj):
            warnings.warn('Implicit collection handling is deprecated. Set '
                            'many=True to serialize a collection.',
                            category=DeprecationWarning)
        # copy declared fields from metaclass
        self.declared_fields = copy.deepcopy(self._declared_fields)
        self.fields = OrderedDict()
        self.__data = None
        self.obj = obj
        self.many = many
        self.opts = self.OPTIONS_CLASS(self.Meta)
        self.only = only or ()
        self.exclude = exclude or ()
        self.prefix = prefix
        self.strict = strict or self.opts.strict
        #: Callable marshalling object
        self.marshal = fields.Marshaller(prefix=self.prefix, strict=self.strict)
        self.extra = extra
        self.context = context
        if isinstance(obj, types.GeneratorType):
            self.obj = list(obj)
        else:
            self.obj = obj
        self._update_fields(obj)
        # If object is passed in, marshal it immediately so that errors are stored
        if self.obj is not None:
            raw_data = self.marshal(self.obj, self.fields, many=self.many)
            if self.extra:
                raw_data.update(self.extra)
            self.__data = self.process_data(raw_data)

    @classmethod
    def factory(cls, *args, **kwargs):
        """Create a factory function that returns an instance of the serializer.
        Can be used to "freeze" the serializer's arguments.

        Example usage: ::

            serialize_user = UserSerializer.factory(strict=True)
            user = User(email='invalidemail')
            serialize_user(user)  # => raises MarshallingError

        :param args: Takes the same positional and keyword arguments as the
            serializer's constructor
        :rtype: A ``functools.partial`` object (from the standard library)
        :return: A function that returns instances of the serializer, fixed with
            the passed arguments.

        .. versionadded:: 0.5.5

        """
        factory_func = functools.partial(cls, *args, **kwargs)
        functools.update_wrapper(factory_func, cls)
        return factory_func

    def _update_fields(self, obj):
        """Update fields based on the passed in object."""
        # if only __init__ param is specified, only return those fields
        if self.only:
            ret = self.__filter_fields(self.only)
            self.__set_field_attrs(ret)
            self.fields = ret
            return self.fields

        if self.opts.fields:
            # Return only fields specified in fields option
            field_names = set(self.opts.fields)
        elif self.opts.additional:
            # Return declared fields + additional fields
            field_names = set(self.declared_fields.keys()) | set(self.opts.additional)
        else:
            field_names = set(self.declared_fields.keys())

        # If "exclude" option or param is specified, remove those fields
        excludes = set(self.opts.exclude) | set(self.exclude)
        if excludes:
            field_names = field_names - excludes
        ret = self.__filter_fields(field_names)
        # Set parents
        self.__set_field_attrs(ret)
        self.fields = ret
        return self.fields

    def __set_field_attrs(self, fields_dict):
        """Set the parents of all field objects in fields_dict to self, and
        set the dateformat specified in ``class Meta``, if necessary.
        """
        for field_name, field_obj in iteritems(fields_dict):
            if not field_obj.parent:
                field_obj.parent = self
            if not field_obj.name:
                field_obj.name = field_name
            if isinstance(field_obj, fields.DateTime):
                if field_obj.dateformat is None:
                    field_obj.dateformat = self.opts.dateformat
        return fields_dict

    def __filter_fields(self, field_names):
        """Return only those field_name:field_obj pairs specified by
        ``field_names``.

        :param set field_names: Field names to include in the final
            return dictionary.
        :returns: An OrderedDict of field_name:field_obj pairs.
        """
        # Convert obj to a dict
        obj_marshallable = utils.to_marshallable_type(self.obj,
            field_names=field_names)
        if obj_marshallable and self.many:
            try:  # Homogeneous collection
                obj_prototype = obj_marshallable[0]
            except IndexError:  # Nothing to serialize
                return self.declared_fields
            obj_dict = utils.to_marshallable_type(obj_prototype,
                field_names=field_names)
        else:
            obj_dict = obj_marshallable
        ret = OrderedDict()
        for key in field_names:
            if key in self.declared_fields:
                ret[key] = self.declared_fields[key]
            else:
                if obj_dict:
                    try:
                        attribute_type = type(obj_dict[key])
                    except KeyError:
                        raise AttributeError(
                            '"{0}" is not a valid field for {1}.'.format(key, self.obj))
                    field_obj = self.TYPE_MAPPING.get(attribute_type, fields.Raw)()
                else:  # Object is None
                    field_obj = fields.Raw()
                # map key -> field (default to Raw)
                ret[key] = field_obj
        return ret

    @property
    def data(self):
        """The serialized data as an :class:`OrderedDict`.
        """
        if not self.__data:  # Cache the data
            raw_data = self.marshal(self.obj, self.fields, many=self.many)
            if self.extra:
                raw_data.update(self.extra)
            self.__data = self.process_data(raw_data)
        return self.__data

    @property
    def json(self):
        """The data as a JSON string."""
        return self.to_json()

    @property
    def errors(self):
        """Dictionary of errors raised during serialization."""
        return self.marshal.errors

    def process_data(self, data):
        """Hook that allows subclasses to modify the final output of the data.

        .. versionadded:: 0.5.5
        """
        return data

    def to_json(self, *args, **kwargs):
        """Return the JSON representation of the data. Takes the same arguments
        as Python's built-in ``json.dumps``.
        """
        ret = self.opts.json_module.dumps(self.data, *args, **kwargs)
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
