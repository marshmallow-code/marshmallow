# -*- coding: utf-8 -*-
"""The :class:`Schema` class, including its metaclass and options (class Meta)."""
from __future__ import absolute_import, unicode_literals

from collections import defaultdict
import copy
import datetime as dt
import decimal
import inspect
import json
import types
import uuid
import warnings
from collections import namedtuple
from functools import partial

from marshmallow import base, fields, utils, class_registry, marshalling
from marshmallow.compat import (with_metaclass, iteritems, text_type,
                                binary_type, OrderedDict)
from marshmallow.orderedset import OrderedSet
from marshmallow.decorators import PRE_DUMP, POST_DUMP, PRE_LOAD, POST_LOAD


#: Return type of :meth:`Schema.dump` including serialized data and errors
MarshalResult = namedtuple('MarshalResult', ['data', 'errors'])
#: Return type of :meth:`Schema.load`, including deserialized data and errors
UnmarshalResult = namedtuple('UnmarshalResult', ['data', 'errors'])

def _get_fields(attrs, field_class, pop=False, ordered=False):
    """Get fields from a class. If ordered=True, fields will sorted by creation index.

    :param attrs: Mapping of class attributes
    :param type field_class: Base field class
    :param bool pop: Remove matching fields
    """
    getter = getattr(attrs, 'pop' if pop else 'get')
    fields = [
        (field_name, getter(field_name))
        for field_name, field_value in list(iteritems(attrs))
        if utils.is_instance_or_subclass(field_value, field_class)
    ]
    if ordered:
        return sorted(
            fields,
            key=lambda pair: pair[1]._creation_index,
        )
    else:
        return fields

# This function allows Schemas to inherit from non-Schema classes and ensures
#   inheritance according to the MRO
def _get_fields_by_mro(klass, field_class, ordered=False):
    """Collect fields from a class, following its method resolution order. The
    class itself is excluded from the search; only its parents are checked. Get
    fields from ``_declared_fields`` if available, else use ``__dict__``.

    :param type klass: Class whose fields to retrieve
    :param type field_class: Base field class
    """
    mro = inspect.getmro(klass)
    # Loop over mro in reverse to maintain correct order of fields
    return sum(
        (
            _get_fields(
                getattr(base, '_declared_fields', base.__dict__),
                field_class,
                ordered=ordered
            )
            for base in mro[:0:-1]
        ),
        [],
    )


class SchemaMeta(type):
    """Metaclass for the Schema class. Binds the declared fields to
    a ``_declared_fields`` attribute, which is a dictionary mapping attribute
    names to field objects. Also sets the ``opts`` class attribute, which is
    the Schema class's ``class Meta`` options.
    """
    FUNC_LISTS = ('__validators__', '__data_handlers__', '__preprocessors__')

    def __new__(mcs, name, bases, attrs):
        meta = attrs.get('Meta')
        ordered = getattr(meta, 'ordered', False)
        if not ordered:
            # Inherit 'ordered' option
            # Warning: We loop through bases instead of MRO because we don't
            # yet have access to the class object
            # (i.e. can't call super before we have fields)
            for base_ in bases:
                if hasattr(base_, 'Meta') and hasattr(base_.Meta, 'ordered'):
                    ordered = base_.Meta.ordered
                    break
            else:
                ordered = False
        cls_fields = _get_fields(attrs, base.FieldABC, pop=True, ordered=ordered)
        klass = super(SchemaMeta, mcs).__new__(mcs, name, bases, attrs)
        inherited_fields = _get_fields_by_mro(klass, base.FieldABC)

        # Use getattr rather than attrs['Meta'] so that we get inheritance for free
        meta = getattr(klass, 'Meta')
        # Set klass.opts in __new__ rather than __init__ so that it is accessible in
        # get_declared_fields
        klass.opts = klass.OPTIONS_CLASS(meta)
        # Add fields specifid in the `include` class Meta option
        cls_fields += list(klass.opts.include.items())

        dict_cls = OrderedDict if ordered else dict
        # Assign _declared_fields on class
        klass._declared_fields = mcs.get_declared_fields(
            klass=klass,
            cls_fields=cls_fields,
            inherited_fields=inherited_fields,
            dict_cls=dict_cls
        )
        return klass

    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """Returns a dictionary of field_name => `Field` pairs declard on the class.
        This is exposed mainly so that plugins can add additional fields, e.g. fields
        computed from class Meta options.

        :param type klass: The class object.
        :param dict cls_fields: The fields declared on the class, including those added
            by the ``include`` class Meta option.
        :param dict inherited_fileds: Inherited fields.
        :param type dict_class: Either `dict` or `OrderedDict`, depending on the whether
            the user specified `ordered=True`.
        """
        return dict_cls(inherited_fields + cls_fields)

    # NOTE: self is the class object
    def __init__(self, name, bases, attrs):
        super(SchemaMeta, self).__init__(name, bases, attrs)
        class_registry.register(name, self)
        self._copy_func_attrs()
        self._resolve_processors()

    def _copy_func_attrs(self):
        """Copy non-shareable class function lists

        Need to copy validators, data handlers, and preprocessors lists so they
        are not shared among subclasses and ancestors.
        """
        for attr in self.FUNC_LISTS:
            attr_copy = copy.copy(getattr(self, attr))
            setattr(self, attr, attr_copy)

    def _resolve_processors(self):
        """Add in the decorated processors

        By doing this after constructing the class, we let standard inheritance
        do all the hard work.
        """
        mro = inspect.getmro(self)
        self.__processors__ = defaultdict(list)
        for attr_name in dir(self):
            # Need to look up the actual descriptor, not whatever might be
            # bound to the class. This needs to come from the __dict__ of the
            # declaring class.
            for parent in mro:
                try:
                    attr = parent.__dict__[attr_name]
                except KeyError:
                    continue
                else:
                    break
            else:
                # In case we didn't find the attribute and didn't break above.
                # We should never hit this - it's just here for completeness
                # to exclude the possibility of attr being undefined.
                continue

            try:
                processor_tags = attr.__marshmallow_tags__
            except AttributeError:
                continue

            for tag in processor_tags:
                # Use name here so we can get the bound method later, in case
                # the processor was a descriptor or something.
                self.__processors__[tag].append(attr_name)


class SchemaOpts(object):
    """class Meta options for the :class:`Schema`. Defines defaults."""

    def __init__(self, meta):
        self.fields = getattr(meta, 'fields', ())
        if not isinstance(self.fields, (list, tuple)):
            raise ValueError("`fields` option must be a list or tuple.")
        self.additional = getattr(meta, 'additional', ())
        if not isinstance(self.additional, (list, tuple)):
            raise ValueError("`additional` option must be a list or tuple.")
        if self.fields and self.additional:
            raise ValueError("Cannot set both `fields` and `additional` options"
                            " for the same Schema.")
        self.exclude = getattr(meta, 'exclude', ())
        if not isinstance(self.exclude, (list, tuple)):
            raise ValueError("`exclude` must be a list or tuple.")
        self.strict = getattr(meta, 'strict', False)
        self.dateformat = getattr(meta, 'dateformat', None)
        self.json_module = getattr(meta, 'json_module', json)
        self.skip_missing = getattr(meta, 'skip_missing', False)
        self.ordered = getattr(meta, 'ordered', False)
        self.index_errors = getattr(meta, 'index_errors', True)
        self.include = getattr(meta, 'include', {})


class BaseSchema(base.SchemaABC):
    """Base schema class with which to define custom schemas.

    Example usage:

    .. code-block:: python

        import datetime as dt
        from marshmallow import Schema, fields

        class Album(object):
            def __init__(self, title, release_date):
                self.title = title
                self.release_date = release_date

        class AlbumSchema(Schema):
            title = fields.Str()
            release_date = fields.Date()

        # Or, equivalently
        class AlbumSchema2(Schema):
            class Meta:
                fields = ("title", "release_date")

        album = Album("Beggars Banquet", dt.date(1968, 12, 6))
        schema = AlbumSchema()
        data, errors = schema.dump(album)
        data  # {'release_date': '1968-12-06', 'title': 'Beggars Banquet'}

    :param dict extra: A dict of extra attributes to bind to the serialized result.
    :param tuple only: A list or tuple of fields to serialize. If `None`, all
        fields will be serialized.
    :param tuple exclude: A list or tuple of fields to exclude from the
        serialized result.
    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    :param bool strict: If `True`, raise errors if invalid data are passed in
        instead of failing silently and storing the errors.
    :param bool many: Should be set to `True` if ``obj`` is a collection
        so that the object will be serialized to a list.
    :param bool skip_missing: If `True`, don't include key:value pairs in
        serialized results if ``value`` is `None`.
    :param dict context: Optional context passed to :class:`fields.Method` and
        :class:`fields.Function` fields.
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
        decimal.Decimal: fields.Decimal,
    }

    OPTIONS_CLASS = SchemaOpts

    #: Custom error handler function. May be `None`.
    __error_handler__ = None

    #  NOTE: The below class attributes must initially be `None` so that
    #  every subclass references a different list of functions

    #: List of registered post-processing functions.
    __data_handlers__ = None
    #: List of registered schema-level validation functions.
    __validators__ = None
    #: List of registered pre-processing functions.
    __preprocessors__ = None
    #: Function used to get values of an object.
    __accessor__ = None

    class Meta(object):
        """Options object for a Schema.

        Example usage: ::

            class Meta:
                fields = ("id", "email", "date_created")
                exclude = ("password", "secret_attribute")

        Available options:

        - ``fields``: Tuple or list of fields to include in the serialized result.
        - ``additional``: Tuple or list of fields to include *in addition* to the
            explicitly declared fields. ``additional`` and ``fields`` are
            mutually-exclusive options.
        - ``include``: Dictionary of additional fields to include in the schema. It is
            usually better to define fields as class variables, but you may need to
            use this option, e.g., if your fields are Python keywords. May be an
            `OrderedDict`.
        - ``exclude``: Tuple or list of fields to exclude in the serialized result.
        - ``dateformat``: Date format for all DateTime fields that do not have their
            date format explicitly specified.
        - ``strict``: If `True`, raise errors during marshalling rather than
            storing them.
        - ``json_module``: JSON module to use for `loads` and `dumps`.
            Defaults to the ``json`` module in the stdlib.
        - ``skip_missing``: If `True`, don't include key:value pairs in
            serialized results if ``value`` is `None`.
        - ``ordered``: If `True`, order serialization output according to the
            order in which fields were declared. Output of `Schema.dump` will be a
            `collections.OrderedDict`.
        - ``index_errors``: If `True`, errors dictionaries will include the index
            of invalid items in a collection.

        .. versionchanged:: 2.0.0
            `__preprocessors__` and `__data_handlers__` are deprecated. Use
            `marshmallow.decorators.pre_load` and `marshmallow.decorators.post_dump` instead.
        """
        pass

    def __init__(self, extra=None, only=(), exclude=(), prefix='', strict=False,
                 many=False, skip_missing=False, context=None):
        # copy declared fields from metaclass
        self.declared_fields = copy.deepcopy(self._declared_fields)
        self.many = many
        self.only = only
        self.exclude = exclude
        self.prefix = prefix
        self.strict = strict or self.opts.strict
        self.skip_missing = skip_missing or self.opts.skip_missing
        self.ordered = self.opts.ordered
        #: Dictionary mapping field_names -> :class:`Field` objects
        self.fields = self.dict_class()
        #: Callable marshalling object
        self._marshal = marshalling.Marshaller(
            prefix=self.prefix
        )
        #: Callable unmarshalling object
        self._unmarshal = marshalling.Unmarshaller()
        self.extra = extra
        self.context = context or {}
        self._update_fields(many=many)

    def __repr__(self):
        return '<{ClassName}(many={self.many}, strict={self.strict})>'.format(
            ClassName=self.__class__.__name__, self=self
        )

    def _postprocess(self, data, many, obj):
        if self.extra:
            if many:
                for each in data:
                    each.update(self.extra)
            else:
                data.update(self.extra)
        if self._marshal.errors and callable(self.__error_handler__):
            self.__error_handler__(self._marshal.errors, obj)

        # invoke registered callbacks
        # NOTE: these callbacks will mutate the data
        if self.__data_handlers__:
            for callback in self.__data_handlers__:
                if callable(callback):
                    data = callback(self, data, obj)
        return data

    @property
    def dict_class(self):
        return OrderedDict if self.ordered else dict

    @property
    def set_class(self):
        return OrderedSet if self.ordered else set

    ##### Handler decorators #####

    @classmethod
    def error_handler(cls, func):
        """Decorator that registers an error handler function for the schema.
        The function receives the :class:`Schema` instance, a dictionary of errors,
        and the serialized object (if serializing data) or data dictionary (if
        deserializing data) as arguments.

        Example: ::

            class UserSchema(Schema):
                email = fields.Email()

            @UserSchema.error_handler
            def handle_errors(schema, errors, obj):
                raise ValueError('An error occurred while marshalling {}'.format(obj))

            user = User(email='invalid')
            UserSchema().dump(user)  # => raises ValueError
            UserSchema().load({'email': 'bademail'})  # raises ValueError

        .. versionadded:: 0.7.0
        """
        cls.__error_handler__ = func
        return func

    @classmethod
    def data_handler(cls, func):
        """Decorator that registers a post-processing function.
        The function receives the :class:`Schema` instance, the serialized
        data, and the original object as arguments and should return the
        processed data.

        Example: ::

            class UserSchema(Schema):
                name = fields.String()

            @UserSchema.data_handler
            def add_surname(schema, data, obj):
                data['surname'] = data['name'].split()[1]
                return data

        .. note::

            You can register multiple handler functions for the same schema.

        .. versionadded:: 0.7.0
        .. deprecated:: 2.0.0
            Use `marshmallow.post_dump` instead.
        """
        warnings.warn(
            'Schema.data_handler is deprecated. Use the marshmallow.post_dump decorator '
            'instead.', category=DeprecationWarning
        )
        cls.__data_handlers__ = cls.__data_handlers__ or []
        cls.__data_handlers__.append(func)
        return func

    @classmethod
    def validator(cls, func):
        """Decorator that registers a schema validation function to be applied during
        deserialization. The function receives the :class:`Schema` instance and the
        input data as arguments and should return `False` if validation fails.

        Example: ::

            class NumberSchema(Schema):
                field_a = fields.Integer()
                field_b = fields.Integer()

            @NumberSchema.validator
            def validate_numbers(schema, input_data):
                return input_data['field_b'] > input_data['field_a']

        A validator may take an optional third argument which will contain the raw input
        data. ::

            @NumberSchema.validator
            def check_unknown_fields(schema, input_data, raw_data):
                for k in raw_data:
                    if k not in schema.fields:
                        raise ValidationError('Unknown field name')

        .. note::

            You can register multiple validators for the same schema.

        .. versionadded:: 1.0
        .. versionchanged:: 2.0
            Validators can receive an optional third argument which is the
            raw input data.
        """
        cls.__validators__ = cls.__validators__ or []
        cls.__validators__.append(func)
        return func

    @classmethod
    def preprocessor(cls, func):
        """Decorator that registers a preprocessing function to be applied during
        deserialization. The function receives the :class:`Schema` instance and the
        input data as arguments and should return the modified dictionary of data.

        Example: ::

            class NumberSchema(Schema):
                field_a = fields.Integer()
                field_b = fields.Integer()

            @NumberSchema.preprocessor
            def add_to_field_a(schema, input_data):
                input_data['field_a'] += 1
                return input_data

        .. note::

            You can register multiple preprocessors for the same schema.

        .. versionadded:: 1.0
        .. deprecated:: 2.0.0
            Use `marshmallow.pre_load` instead.
        """
        warnings.warn(
            'Schema.preprocessor is deprecated. Use the marshmallow.pre_load decorator '
            'instead.', category=DeprecationWarning
        )
        cls.__preprocessors__ = cls.__preprocessors__ or []
        cls.__preprocessors__.append(func)
        return func

    @classmethod
    def accessor(cls, func):
        """Decorator that registers a function for pulling values from an object
        to serialize. The function receives the :class:`Schema` instance, the
        ``key`` of the value to get, the ``obj`` to serialize, and an optional
        ``default`` value.
        """
        cls.__accessor__ = func
        return func

    ##### Serialization/Deserialization API #####

    def dump(self, obj, many=None, update_fields=True, **kwargs):
        """Serialize an object to native Python data types according to this
        Schema's fields.

        :param obj: The object to serialize.
        :param bool many: Whether to serialize `obj` as a collection. If `None`, the value
            for `self.many` is used.
        :param bool update_fields: Whether to update the schema's field classes. Typically
            set to `True`, but may be `False` when serializing a homogenous collection.
            This parameter is used by `fields.Nested` to avoid multiple updates.
        :return: A tuple of the form (``data``, ``errors``)
        :rtype: `MarshalResult`, a `collections.namedtuple`

        .. versionadded:: 1.0.0
        """
        many = self.many if many is None else bool(many)
        if not many and utils.is_collection(obj) and not utils.is_keyed_tuple(obj):
            warnings.warn('Implicit collection handling is deprecated. Set '
                            'many=True to serialize a collection.',
                            category=DeprecationWarning)
        if isinstance(obj, types.GeneratorType):
            obj = list(obj)
        if update_fields:
            self._update_fields(obj, many=many)

        obj = self._invoke_dump_processors(PRE_DUMP, obj, many)

        preresult = self._marshal(
            obj,
            self.fields,
            many=many,
            strict=self.strict,
            skip_missing=self.skip_missing,
            accessor=self.__accessor__,
            dict_class=self.dict_class,
            index_errors=self.opts.index_errors,
            **kwargs
        )
        result = self._postprocess(preresult, many, obj=obj)
        errors = self._marshal.errors

        result = self._invoke_dump_processors(POST_DUMP, result, many)

        return MarshalResult(result, errors)

    def dumps(self, obj, many=None, update_fields=True, *args, **kwargs):
        """Same as :meth:`dump`, except return a JSON-encoded string.

        :param obj: The object to serialize.
        :param bool many: Whether to serialize `obj` as a collection. If `None`, the value
            for `self.many` is used.
        :param bool update_fields: Whether to update the schema's field classes. Typically
            set to `True`, but may be `False` when serializing a homogenous collection.
            This parameter is used by `fields.Nested` to avoid multiple updates.
        :return: A tuple of the form (``data``, ``errors``)
        :rtype: `MarshalResult`, a `collections.namedtuple`

        .. versionadded:: 1.0.0
        """
        deserialized, errors = self.dump(obj, many=many, update_fields=update_fields)
        ret = self.opts.json_module.dumps(deserialized, *args, **kwargs)
        return MarshalResult(ret, errors)

    def load(self, data, many=None):
        """Deserialize a data structure to an object defined by this Schema's
        fields and :meth:`make_object`.

        :param dict data: The data to deserialize.
        :param bool many: Whether to deserialize `data` as a collection. If `None`, the
            value for `self.many` is used.
        :return: A tuple of the form (``data``, ``errors``)
        :rtype: `UnmarshalResult`, a `collections.namedtuple`

        .. versionadded:: 1.0.0
        """
        result, errors = self._do_load(data, many, postprocess=True)
        return UnmarshalResult(data=result, errors=errors)

    def loads(self, json_data, many=None, *args, **kwargs):
        """Same as :meth:`load`, except it takes a JSON string as input.

        :param str json_data: A JSON string of the data to deserialize.
        :param bool many: Whether to deserialize `obj` as a collection. If `None`, the
            value for `self.many` is used.
        :return: A tuple of the form (``data``, ``errors``)
        :rtype: `UnmarshalResult`, a `collections.namedtuple`

        .. versionadded:: 1.0.0
        """
        data = self.opts.json_module.loads(json_data, *args, **kwargs)
        return self.load(data, many=many)

    def validate(self, data, many=None):
        """Validate `data` against the schema, returning a dictionary of
        validation errors.

        :param dict data: The data to validate.
        :param bool many: Whether to validate `data` as a collection. If `None`, the
            value for `self.many` is used.
        :return: A dictionary of validation errors.
        :rtype: dict

        .. versionadded:: 1.1.0
        """
        _, errors = self._do_load(data, many, postprocess=False)
        return errors

    def make_object(self, data):
        """Override-able method that defines how to create the final deserialization
        output. Defaults to noop (i.e. just return ``data`` as is).

        :param dict data: The deserialized data.

        .. versionadded:: 1.0.0
        """
        return data

    ##### Private Helpers #####

    def _do_load(self, data, many=None, postprocess=True):
        """Deserialize `data`, returning the deserialized result and a dictonary of
        validation errors.

        :param data: The data to deserialize.
        :param bool many: Whether to deserialize `data` as a collection. If `None`, the
            value for `self.many` is used.
        :param bool postprocess: Whether to postprocess the data with `make_object`.
        :return: A tuple of the form (`data`, `errors`)
        """
        many = self.many if many is None else bool(many)

        data = self._invoke_load_processors(PRE_LOAD, data, many)

        # Bind self as the first argument of validators and preprocessors
        if self.__validators__:
            validators = [partial(func, self)
                         for func in self.__validators__]
        else:
            validators = []
        if self.__preprocessors__:
            preprocessors = [partial(func, self)
                            for func in self.__preprocessors__]
        else:
            preprocessors = []

        postprocess_funcs = [self.make_object] if postprocess else []
        result = self._unmarshal(
            data,
            self.fields,
            many=many,
            strict=self.strict,
            validators=validators,
            preprocess=preprocessors,
            postprocess=postprocess_funcs,
            dict_class=self.dict_class,
            index_errors=self.opts.index_errors,
        )
        errors = self._unmarshal.errors
        if errors and callable(self.__error_handler__):
            self.__error_handler__(errors, data)

        result = self._invoke_load_processors(POST_LOAD, result, many)

        return result, errors

    def _update_fields(self, obj=None, many=False):
        """Update fields based on the passed in object."""
        if self.only:
            # Return only fields specified in fields option
            field_names = self.set_class(self.only)
        elif self.opts.fields:
            # Return fields specified in fields option
            field_names = self.set_class(self.opts.fields)
        elif self.opts.additional:
            # Return declared fields + additional fields
            field_names = (self.set_class(self.declared_fields.keys()) |
                            self.set_class(self.opts.additional))
        else:
            field_names = self.set_class(self.declared_fields.keys())

        # If "exclude" option or param is specified, remove those fields
        excludes = set(self.opts.exclude) | set(self.exclude)
        if excludes:
            field_names = field_names - excludes
        ret = self.__filter_fields(field_names, obj, many=many)
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

    def __filter_fields(self, field_names, obj, many=False):
        """Return only those field_name:field_obj pairs specified by
        ``field_names``.

        :param set field_names: Field names to include in the final
            return dictionary.
        :returns: An dict of field_name:field_obj pairs.
        """
        # Convert obj to a dict
        obj_marshallable = utils.to_marshallable_type(obj,
            field_names=field_names)
        if obj_marshallable and many:
            try:  # Homogeneous collection
                obj_prototype = obj_marshallable[0]
            except IndexError:  # Nothing to serialize
                return self.declared_fields
            obj_dict = utils.to_marshallable_type(obj_prototype,
                field_names=field_names)
        else:
            obj_dict = obj_marshallable
        ret = self.dict_class()
        for key in field_names:
            if key in self.declared_fields:
                ret[key] = self.declared_fields[key]
            else:
                if obj_dict:
                    try:
                        attribute_type = type(obj_dict[key])
                    except KeyError:
                        raise AttributeError(
                            '"{0}" is not a valid field for {1}.'.format(key, obj))
                    field_obj = self.TYPE_MAPPING.get(attribute_type, fields.Field)()
                else:  # Object is None
                    field_obj = fields.Field()
                # map key -> field (default to Raw)
                ret[key] = field_obj
        return ret

    def _invoke_dump_processors(self, tag_name, data, many):
        # The raw post-dump processors may do things like add an envelope, so
        # invoke those after invoking the non-raw processors which will expect
        # to get a list of items.
        data = self._invoke_processors(tag_name, raw=False, data=data, many=many)
        data = self._invoke_processors(tag_name, raw=True, data=data, many=many)
        return data

    def _invoke_load_processors(self, tag_name, data, many):
        # This has to invert the order of the dump processors, so run the raw
        # processors first.
        data = self._invoke_processors(tag_name, raw=True, data=data, many=many)
        data = self._invoke_processors(tag_name, raw=False, data=data, many=many)
        return data

    def _invoke_processors(self, tag_name, raw, data, many):
        for attr_name in self.__processors__[(tag_name, raw)]:
            # This will be a bound method.
            processor = getattr(self, attr_name)

            # It's probably not worth the extra LoC to hoist this branch out of
            # the loop.
            if raw:
                data = utils.if_none(processor(data, many), data)
            elif many:
                data = [utils.if_none(processor(item), item) for item in data]
            else:
                data = utils.if_none(processor(data), data)

        return data


class Schema(with_metaclass(SchemaMeta, BaseSchema)):
    __doc__ = BaseSchema.__doc__
