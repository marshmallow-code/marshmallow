# -*- coding: utf-8 -*-
"""Utility classes and values used for marshalling and unmarshalling objects to
and from primitive types.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals
import collections

from marshmallow.utils import (
    EXCLUDE, INCLUDE, RAISE, is_collection, missing, set_value,
)
from marshmallow.compat import iteritems
from marshmallow.exceptions import ValidationError

__all__ = [
    'Marshaller',
    'Unmarshaller',
]

# Key used for schema-level validation errors
SCHEMA = '_schema'
# Key used for field-level validation errors on nested fields
FIELD = '_field'

class ErrorStore(object):

    def __init__(self):
        #: Dictionary of errors stored during serialization
        self.errors = {}
        #: List of field_names which have validation errors
        self.error_field_names = []
        #: True while (de)serializing a collection
        self._pending = False
        #: Dictionary of extra kwargs from user raised exception
        self.error_kwargs = {}

    def get_errors(self, index=None):
        return self.errors if index is None else self.errors.setdefault(index, {})

    def store_error(self, field_name, messages, index=None):
        self.error_field_names.append(field_name)
        errors = self.get_errors(index=index)
        # Warning: Mutation!
        if isinstance(messages, dict):
            errors[field_name] = messages
        elif isinstance(errors.get(field_name), dict):
            errors[field_name].setdefault(FIELD, []).extend(messages)
        else:
            errors.setdefault(field_name, []).extend(messages)

    def store_validation_error(self, field_names, error, index=None):
        self.error_kwargs.update(error.kwargs)
        for field_name in field_names:
            self.store_error(field_name, error.messages, index=index)
        # When a Nested field fails validation, the marshalled data is stored
        # on the ValidationError's valid_data attribute
        return error.valid_data or missing

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
        except ValidationError as error:
            return self.store_validation_error((field_name,), error, index)
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
            if self.errors:
                raise ValidationError(
                    self.errors,
                    field_names=self.error_field_names,
                    data=ret,
                )
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
                index=(index if index_errors else None),
            )
            if value is missing:
                continue
            items.append((key, value))
        ret = dict_class(items)
        if self.errors and not self._pending:
            raise ValidationError(
                self.errors,
                field_names=self.error_field_names,
                data=ret,
            )
        return ret

    # Make an instance callable
    __call__ = serialize


class Unmarshaller(ErrorStore):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """

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
            # Store or reraise errors
            field_names = err.field_names or [SCHEMA]
            self.store_validation_error(field_names, err, index=index)

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
            will be ignored.
        :param unknown: Whether to exclude, include, or raise an error for unknown
            fields in the data. Use `EXCLUDE`, `INCLUDE` or `RAISE`.
        :param type dict_class: Dictionary class used to construct the output.
        :param bool index_errors: Whether to store the index of invalid items in
            ``self.errors`` when ``many=True``.
        :param int index: Index of the item being serialized (for storing errors) if
            serializing a collection, otherwise `None`.
        :return: A dictionary of the deserialized data.
        """
        if many:
            if not is_collection(data):
                self.store_error(SCHEMA, ('Invalid input type.', ), index=index)
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
        if not isinstance(data, collections.Mapping):
            self.store_error(SCHEMA, ('Invalid input type.', ), index=index)
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
                getter = lambda val: field_obj.deserialize(val, field_name, data)
                value = self.call_and_store(
                    getter_func=getter,
                    data=raw_value,
                    field_name=field_name,
                    index=(index if index_errors else None),
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
                            key,
                            ('Unknown field.',),
                            (index if index_errors else None),
                        )
        return ret

    # Make an instance callable
    __call__ = deserialize
