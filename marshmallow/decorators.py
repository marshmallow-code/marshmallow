# -*- coding: utf-8 -*-
"""Decorators for registering schema pre-processing and post-processing methods.
These should be imported from the top-level `marshmallow` module.

Example: ::

    from marshmallow import (
        Schema, pre_load, pre_dump, post_load, validates_schema,
        validates, fields, ValidationError
    )

    class UserSchema(Schema):

        email = fields.Str(required=True)
        age = fields.Integer(required=True)

        @post_load
        def lowerstrip_email(self, item):
            item['email'] = item['email'].lower().strip()
            return item

        @pre_load(raw=True)
        def remove_envelope(self, data, many):
            namespace = 'results' if many else 'result'
            return data[namespace]

        @post_dump(raw=True):
        def add_envelope(self, data, many):
            namespace = 'results' if many else 'result'
            return {namespace: data}

        @validates_schema
        def validate_email(self, data):
            if len(data['email']) < 3:
                raise ValidationError('Email must be more than 3 characters', 'email')

        @validates('age')
        def validate_age(self, data):
            if data < 14:
                raise ValidationError('Too young!')

.. warning::
    The invocation order of decorated methods of the same type is not guaranteed.
    If you need to guarantee order of different processing steps, you should put
    them in the same processing method.
"""
from __future__ import unicode_literals


PRE_DUMP = 'pre_dump'
POST_DUMP = 'post_dump'
PRE_LOAD = 'pre_load'
POST_LOAD = 'post_load'
VALIDATES = 'validates'
VALIDATES_SCHEMA = 'validates_schema'


def validates(field_name):
    """Register a field validator.

    :param str field_name: Name of the field that the method validates.
    """
    return tag_processor(VALIDATES, None, False, field_name=field_name)


def validates_schema(fn=None, raw=False, pass_original=False):
    """Register a schema-level validates_schema method.

    By default, receives a single object at a time, regardless of whether ``many=True``
    is passed to the `Schema`. If ``raw=True``, the raw data (which may be a collection)
    and the value for ``many`` is passed.

    If ``pass_original=True``, the original data (before unmarshalling) will be passed as
    an additional argument to the method.
    """
    return tag_processor(VALIDATES_SCHEMA, fn, raw, pass_original=pass_original)


def pre_dump(fn=None, raw=False):
    """Register a method to invoke before serializing an object. The method
    receives the object to be serialized and returns the processed object.

    By default, receives a single object at a time, regardless of whether ``many=True``
    is passed to the `Schema`. If ``raw=True``, the raw data (which may be a collection)
    and the value for ``many`` is passed.
    """
    return tag_processor(PRE_DUMP, fn, raw)


def post_dump(fn=None, raw=False):
    """Register a method to invoke after serializing an object. The method
    receives the serialized object and returns the processed object.

    By default, receives a single object at a time, transparently handling the ``many``
    argument passed to the Schema. If ``raw=True``, the raw data
    (which may be a collection) and the value for ``many`` is passed.
    """
    return tag_processor(POST_DUMP, fn, raw)


def pre_load(fn=None, raw=False):
    """Register a method to invoke before deserializing an object. The method
    receives the data to be deserialized and returns the processed data.

    By default, receives a single datum at a time, transparently handling the ``many``
    argument passed to the Schema. If ``raw=True``, the raw data
    (which may be a collection) and the value for ``many`` is passed.
    """
    return tag_processor(PRE_LOAD, fn, raw)


def post_load(fn=None, raw=False):
    """Register a method to invoke after deserializing an object. The method
    receives the deserialized data and returns the processed data.

    By default, receives a single datum at a time, transparently handling the ``many``
    argument passed to the Schema. If ``raw=True``, the raw data
    (which may be a collection) and the value for ``many`` is passed.
    """
    return tag_processor(POST_LOAD, fn, raw)


class _StaticProcessorMethod(staticmethod):
    """Allows setting attributes on a staticmethod"""
    pass


class _ClassProcessorMethod(classmethod):
    """Allows setting attributes on a classmethod"""
    pass


def tag_processor(tag_name, fn, raw, **kwargs):
    """Tags decorated processor function to be picked up later

    :return: Decorated function if supplied, else this decorator with its args
        bound.
    """
    if fn is None:  # Allow decorator to be used with no arguments
        return lambda fn_actual: tag_processor(tag_name, fn_actual, raw, **kwargs)

    # Special-case rewrapping staticmethod and classmethod, because we can't
    # directly set attributes on those.
    if isinstance(fn, staticmethod):
        try:
            unwrapped = fn.__func__
        except AttributeError:
            # For Python 2.6.
            unwrapped = fn.__get__(True)
        fn = _StaticProcessorMethod(unwrapped)
    elif isinstance(fn, classmethod):
        try:
            unwrapped = fn.__func__
        except AttributeError:
            # For Python 2.6.
            unwrapped = fn.__get__(True).im_func
        fn = _ClassProcessorMethod(unwrapped)

    # Set a marshmallow_tags attribute instead of wrapping in some class,
    # because I still want this to end up as a normal (unbound) method.
    try:
        marshmallow_tags = fn.__marshmallow_tags__
    except AttributeError:
        fn.__marshmallow_tags__ = marshmallow_tags = set()
    # Also save the kwargs for the tagged function on
    # __marshmallow_kwargs__, keyed by (<tag_name>, <raw>)
    try:
        marshmallow_kwargs = fn.__marshmallow_kwargs__
    except AttributeError:
        fn.__marshmallow_kwargs__ = marshmallow_kwargs = {}
    marshmallow_tags.add((tag_name, raw))
    marshmallow_kwargs[(tag_name, raw)] = kwargs

    return fn
