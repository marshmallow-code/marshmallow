# -*- coding: utf-8 -*-
"""Utilities for storing collections of error messages.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals

from marshmallow.utils import missing
from marshmallow.compat import iteritems
from marshmallow.exceptions import ValidationError, SCHEMA


class ErrorStore(object):

    def __init__(self):
        #: Dictionary of errors stored during serialization
        self.errors = {}
        #: True while (de)serializing a collection
        self._pending = False
        #: Dictionary of extra kwargs from user raised exception
        self.error_kwargs = {}

    def store_error(self, messages, field_name=SCHEMA, index=None):
        # field error  -> store/merge error messages under field name key
        # schema error -> if string or list, store/merge under _schema key
        #              -> if dict, store/merge with other top-level keys
        if field_name != SCHEMA or not isinstance(messages, dict):
            messages = {field_name: messages}
        if index is not None:
            messages = {index: messages}
        self.errors = merge_errors(self.errors, messages)

    def call_and_store(self, getter_func, data, field_name, index=None):
        """Call ``getter_func`` with ``data`` as its argument, and store any `ValidationErrors`.

        :param callable getter_func: Function for getting the serialized/deserialized
            value from ``data``.
        :param data: The data passed to ``getter_func``.
        :param str field_name: Field name.
        :param int index: Index of the item being validated, if validating a collection,
            otherwise `None`.
        """
        try:
            value = getter_func(data)
        except ValidationError as err:
            self.error_kwargs.update(err.kwargs)
            self.store_error(err.messages, field_name, index=index)
            # When a Nested field fails validation, the marshalled data is stored
            # on the ValidationError's valid_data attribute
            return err.valid_data or missing
        return value


def merge_errors(errors1, errors2):
    """Deeply merge two error messages

    Error messages can be string, list of strings or dict of error messages
    (recursively). Format is the same as accepted by :exc:`ValidationError`.
    Returns new error messages.
    """
    if not errors1:
        return errors2
    if not errors2:
        return errors1
    if isinstance(errors1, list):
        if isinstance(errors2, list):
            return errors1 + errors2
        if isinstance(errors2, dict):
            return dict(
                errors2,
                **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
            )
        return errors1 + [errors2]
    if isinstance(errors1, dict):
        if isinstance(errors2, list):
            return dict(
                errors1,
                **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
            )
        if isinstance(errors2, dict):
            errors = dict(errors1)
            for key, val in iteritems(errors2):
                if key in errors:
                    errors[key] = merge_errors(errors[key], val)
                else:
                    errors[key] = val
            return errors
        return dict(
            errors1,
            **{SCHEMA: merge_errors(errors1.get(SCHEMA), errors2)}
        )
    if isinstance(errors2, list):
        return [errors1] + errors2 if errors2 else errors1
    if isinstance(errors2, dict):
        return dict(
            errors2,
            **{SCHEMA: merge_errors(errors1, errors2.get(SCHEMA))}
        )
    return [errors1, errors2]
