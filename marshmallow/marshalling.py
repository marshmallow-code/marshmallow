# -*- coding: utf-8 -*-
"""Utility classes and values used for marshalling and unmarshalling objects to
and from primitive types.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals

from marshmallow.utils import (
    EXCLUDE, INCLUDE, RAISE, is_collection, missing, set_value,
)
from marshmallow.compat import iteritems, Mapping
from marshmallow.exceptions import ValidationError, SCHEMA
from marshmallow.fields import Nested

__all__ = [
    'Marshaller',
    'Unmarshaller',
]


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


class Marshaller(ErrorStore):
    """Callable class responsible for serializing data and storing errors."""

    def serialize(
        self, obj, fields_dict, many=False,
        accessor=None, dict_class=dict, index_errors=True,
        index=None,
    ):
        """Takes raw data (a dict, list, or other object) and a dict of
        fields to output and serializes the data based on those fields.

        :param obj: The actual object(s) from which the fields are taken from
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be serialized as
            a collection.
        :param callable accessor: Function to use for getting values from ``obj``.
        :param type dict_class: Dictionary class used to construct the output.
        :param bool index_errors: Whether to store the index of invalid items in
            ``self.errors`` when ``many=True``.
        :param int index: Index of the item being serialized (for storing errors) if
            serializing a collection, otherwise `None`.
        :return: A dictionary of the marshalled data

        .. versionchanged:: 1.0.0
            Renamed from ``marshal``.
        """
        index = index if index_errors else None
        if many and obj is not None:
            self._pending = True
            ret = [
                self.serialize(
                    d, fields_dict, many=False,
                    dict_class=dict_class, accessor=accessor,
                    index=idx, index_errors=index_errors,
                )
                for idx, d in enumerate(obj)
            ]
            self._pending = False
            return ret
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            if getattr(field_obj, 'load_only', False):
                continue
            key = field_obj.data_key or attr_name
            getter = lambda d: field_obj.serialize(attr_name, d, accessor=accessor)
            value = self.call_and_store(
                getter_func=getter,
                data=obj,
                field_name=key,
                index=index,
            )
            if value is missing:
                continue
            items.append((key, value))
        ret = dict_class(items)
        return ret

    # Make an instance callable
    __call__ = serialize


class Unmarshaller(ErrorStore):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """
    _default_error_messages = {
        'type': 'Invalid input type.',
        'unknown': 'Unknown field.'
    }

    def __init__(self, error_messages=None):
        super(Unmarshaller, self).__init__()
        messages = {}
        messages.update(self._default_error_messages)
        messages.update(error_messages or {})
        self.error_messages = messages

    def run_validator(
        self, validator_func, output,
        original_data, fields_dict, index=None,
        many=False, pass_original=False,
    ):
        try:
            if pass_original:  # Pass original, raw data (before unmarshalling)
                validator_func(output, original_data)
            else:
                validator_func(output)
        except ValidationError as err:
            self.error_kwargs.update(err.kwargs)
            self.store_error(err.messages, err.field_name, index=index)

    def deserialize(
        self, data, fields_dict, many=False, partial=False,
        unknown=RAISE, dict_class=dict, index_errors=True, index=None,
    ):
        """Deserialize ``data`` based on the schema defined by ``fields_dict``.

        :param dict data: The data to deserialize.
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be deserialized as
            a collection.
        :param bool|tuple partial: Whether to ignore missing fields. If its
            value is an iterable, only missing fields listed in that iterable
            will be ignored. Use dot delimiters to specify nested fields.
        :param unknown: Whether to exclude, include, or raise an error for unknown
            fields in the data. Use `EXCLUDE`, `INCLUDE` or `RAISE`.
        :param type dict_class: Dictionary class used to construct the output.
        :param bool index_errors: Whether to store the index of invalid items in
            ``self.errors`` when ``many=True``.
        :param int index: Index of the item being serialized (for storing errors) if
            serializing a collection, otherwise `None`.
        :return: A dictionary of the deserialized data.
        """
        index = index if index_errors else None
        if many:
            if not is_collection(data):
                self.store_error([self.error_messages['type']], index=index)
                ret = []
            else:
                self._pending = True
                ret = [
                    self.deserialize(
                        d, fields_dict, many=False,
                        partial=partial, unknown=unknown,
                        dict_class=dict_class, index=idx,
                        index_errors=index_errors,
                    )
                    for idx, d in enumerate(data)
                ]
                self._pending = False
            return ret
        ret = dict_class()
        # Check data is a dict
        if not isinstance(data, Mapping):
            self.store_error([self.error_messages['type']], index=index)
        else:
            partial_is_collection = is_collection(partial)
            for attr_name, field_obj in iteritems(fields_dict):
                if field_obj.dump_only:
                    continue
                field_name = attr_name
                if field_obj.data_key:
                    field_name = field_obj.data_key
                raw_value = data.get(field_name, missing)
                if raw_value is missing:
                    # Ignore missing field if we're allowed to.
                    if (
                        partial is True or
                        (partial_is_collection and attr_name in partial)
                    ):
                        continue
                d_kwargs = {}
                if isinstance(field_obj, Nested):
                    # Allow partial loading of nested schemas.
                    if partial_is_collection:
                        prefix = field_name + '.'
                        len_prefix = len(prefix)
                        sub_partial = [f[len_prefix:]
                                       for f in partial if f.startswith(prefix)]
                    else:
                        sub_partial = partial
                    d_kwargs['partial'] = sub_partial
                getter = lambda val: field_obj.deserialize(
                    val, field_name,
                    data, **d_kwargs
                )
                value = self.call_and_store(
                    getter_func=getter,
                    data=raw_value,
                    field_name=field_name,
                    index=index,
                )
                if value is not missing:
                    key = fields_dict[attr_name].attribute or attr_name
                    set_value(ret, key, value)
            if unknown != EXCLUDE:
                fields = {
                    field_obj.data_key or field_name
                    for field_name, field_obj in fields_dict.items()
                    if not field_obj.dump_only
                }
                for key in set(data) - fields:
                    value = data[key]
                    if unknown == INCLUDE:
                        set_value(ret, key, value)
                    elif unknown == RAISE:
                        self.store_error(
                            [self.error_messages['unknown']],
                            key,
                            (index if index_errors else None),
                        )
        return ret

    # Make an instance callable
    __call__ = deserialize


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
