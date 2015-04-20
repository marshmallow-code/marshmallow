# -*- coding: utf-8 -*-
"""Decorators for registering schema pre-processing and post-processing methods.
These should be imported from the top-level `marshmallow` module.

Example: ::

    from marshmallow import Schema, pre_load, pre_dump, post_load

    class UserSchema(Schema):

        email = fields.Str(required=True)

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

.. warning::
    The invocation order of decorated methods of the same type is not guaranteed.
    If you need to guarantee order of different processing steps, you should put
    them in the same processing method.
"""
PRE_DUMP = 'pre_dump'
POST_DUMP = 'post_dump'
PRE_LOAD = 'pre_load'
POST_LOAD = 'post_load'


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


def tag_processor(tag_name, fn, raw):
    """Tags decorated processor function to be picked up later

    :return: Decorated function if supplied, else this decorator with its args
        bound.
    """
    if fn is None:  # Allow decorator to be used with no arguments
        return lambda fn_actual: tag_processor(tag_name, fn_actual, raw)

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
    marshmallow_tags.add((tag_name, raw))

    return fn
