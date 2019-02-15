# -*- coding: utf-8 -*-
"""Utility classes and values used for marshalling and unmarshalling objects to
and from primitive types.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals

from marshmallow.utils import is_collection, missing, set_value
from marshmallow.compat import text_type, iteritems
from marshmallow.exceptions import (
    ValidationError,
)

__all__ = [
    'Marshaller',
    'Unmarshaller',
]

# Key used for field-level validation errors on nested fields
FIELD = '_field'

class ErrorStore(object):

    def __init__(self):
        #: Dictionary of errors stored during serialization
        self.errors = {}
        #: List of `Field` objects which have validation errors
        self.error_fields = []
        #: List of field_names which have validation errors
        self.error_field_names = []
        #: True while (de)serializing a collection
        self._pending = False
        #: Dictionary of extra kwargs from user raised exception
        self.error_kwargs = {}

    def get_errors(self, index=None):
        if index is not None:
            errors = self.errors.get(index, {})
            self.errors[index] = errors
        else:
            errors = self.errors
        return errors

    def call_and_store(self, getter_func, data, field_name, field_obj, index=None):
        """Call ``getter_func`` with ``data`` as its argument, and store any `ValidationErrors`.

        :param callable getter_func: Function for getting the serialized/deserialized
            value from ``data``.
        :param data: The data passed to ``getter_func``.
        :param str field_name: Field name.
        :param FieldABC field_obj: Field object that performs the
            serialization/deserialization behavior.
        :param int index: Index of the item being validated, if validating a collection,
            otherwise `None`.
        """
        try:
            value = getter_func(data)
        except ValidationError as err:  # Store validation errors
            self.error_kwargs.update(err.kwargs)
            self.error_fields.append(field_obj)
            self.error_field_names.append(field_name)
            errors = self.get_errors(index=index)
            # Warning: Mutation!
            if isinstance(err.messages, dict):
                errors[field_name] = err.messages
            elif isinstance(errors.get(field_name), dict):
                errors[field_name].setdefault(FIELD, []).extend(err.messages)
            else:
                errors.setdefault(field_name, []).extend(err.messages)
            # When a Nested field fails validation, the marshalled data is stored
            # on the ValidationError's data attribute
            value = err.data or missing
        return value

class Marshaller(ErrorStore):
    """Callable class responsible for serializing data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    """
    def __init__(self, prefix=''):
        self.prefix = prefix
        ErrorStore.__init__(self)

    def serialize(self, obj, fields_dict, many=False,
                  accessor=None, dict_class=dict, index_errors=True, index=None):
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
            ret = [self.serialize(d, fields_dict, many=False,
                                    dict_class=dict_class, accessor=accessor,
                                    index=idx, index_errors=index_errors)
                    for idx, d in enumerate(obj)]
            self._pending = False
            if self.errors:
                raise ValidationError(
                    self.errors,
                    field_names=self.error_field_names,
                    fields=self.error_fields,
                    data=ret,
                )
            return ret
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            if getattr(field_obj, 'load_only', False):
                continue

            key = ''.join([self.prefix or '', field_obj.dump_to or attr_name])

            getter = lambda d: field_obj.serialize(attr_name, d, accessor=accessor)
            value = self.call_and_store(
                getter_func=getter,
                data=obj,
                field_name=key,
                field_obj=field_obj,
                index=(index if index_errors else None)
            )
            if value is missing:
                continue
            items.append((key, value))
        ret = dict_class(items)
        if self.errors and not self._pending:
            raise ValidationError(
                self.errors,
                field_names=self.error_field_names,
                fields=self.error_fields,
                data=ret
            )
        return ret

    # Make an instance callable
    __call__ = serialize


# Key used for schema-level validation errors
SCHEMA = '_schema'

class Unmarshaller(ErrorStore):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """

    default_schema_validation_error = 'Invalid data.'

    def run_validator(self, validator_func, output,
            original_data, fields_dict, index=None,
            many=False, pass_original=False):
        try:
            if pass_original:  # Pass original, raw data (before unmarshalling)
                res = validator_func(output, original_data)
            else:
                res = validator_func(output)
            if res is False:
                raise ValidationError(self.default_schema_validation_error)
        except ValidationError as err:
            errors = self.get_errors(index=index)
            self.error_kwargs.update(err.kwargs)
            # Store or reraise errors
            if err.field_names:
                field_names = err.field_names
                field_objs = [fields_dict[each] if each in fields_dict else None
                              for each in field_names]
            else:
                field_names = [SCHEMA]
                field_objs = []
            self.error_field_names = field_names
            self.error_fields = field_objs
            for field_name in field_names:
                if isinstance(err.messages, (list, tuple)):
                    # self.errors[field_name] may be a dict if schemas are nested
                    if isinstance(errors.get(field_name), dict):
                        errors[field_name].setdefault(
                            SCHEMA, []
                        ).extend(err.messages)
                    else:
                        errors.setdefault(field_name, []).extend(err.messages)
                elif isinstance(err.messages, dict):
                    errors.setdefault(field_name, []).append(err.messages)
                else:
                    errors.setdefault(field_name, []).append(text_type(err))

    def deserialize(self, data, fields_dict, many=False, partial=False,
            dict_class=dict, index_errors=True, index=None):
        """Deserialize ``data`` based on the schema defined by ``fields_dict``.

        :param dict data: The data to deserialize.
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be deserialized as
            a collection.
        :param bool|tuple partial: Whether to ignore missing fields. If its
            value is an iterable, only missing fields listed in that iterable
            will be ignored.
        :param type dict_class: Dictionary class used to construct the output.
        :param bool index_errors: Whether to store the index of invalid items in
            ``self.errors`` when ``many=True``.
        :param int index: Index of the item being serialized (for storing errors) if
            serializing a collection, otherwise `None`.
        :return: A dictionary of the deserialized data.
        """
        if many and data is not None:
            if not is_collection(data):
                errors = self.get_errors(index=index)
                self.error_field_names.append(SCHEMA)
                errors[SCHEMA] = ['Invalid input type.']
                ret = []
            else:
                self._pending = True
                ret = [self.deserialize(d, fields_dict, many=False,
                            partial=partial, dict_class=dict_class,
                            index=idx, index_errors=index_errors)
                        for idx, d in enumerate(data)]

                self._pending = False
                if self.errors:
                    raise ValidationError(
                        self.errors,
                        field_names=self.error_field_names,
                        fields=self.error_fields,
                        data=ret,
                    )
            return ret
        if data is not None:
            partial_is_collection = is_collection(partial)
            ret = dict_class()
            for attr_name, field_obj in iteritems(fields_dict):
                if field_obj.dump_only:
                    continue
                try:
                    raw_value = data.get(attr_name, missing)
                except AttributeError:  # Input data is not a dict
                    errors = self.get_errors(index=index)
                    msg = field_obj.error_messages['type'].format(
                        input=data, input_type=data.__class__.__name__
                    )
                    self.error_field_names = [SCHEMA]
                    self.error_fields = []
                    errors = self.get_errors()
                    errors.setdefault(SCHEMA, []).append(msg)
                    # Input data type is incorrect, so we can bail out early
                    break
                field_name = attr_name
                if raw_value is missing and field_obj.load_from:
                    field_name = field_obj.load_from
                    raw_value = data.get(field_obj.load_from, missing)
                if raw_value is missing:
                    # Ignore missing field if we're allowed to.
                    if (
                        partial is True or
                        (partial_is_collection and attr_name in partial)
                    ):
                        continue
                    _miss = field_obj.missing
                    raw_value = _miss() if callable(_miss) else _miss
                if raw_value is missing and not field_obj.required:
                    continue

                getter = lambda val: field_obj.deserialize(
                    val,
                    field_obj.load_from or attr_name,
                    data
                )
                value = self.call_and_store(
                    getter_func=getter,
                    data=raw_value,
                    field_name=field_name,
                    field_obj=field_obj,
                    index=(index if index_errors else None)
                )
                if value is not missing:
                    key = fields_dict[attr_name].attribute or attr_name
                    set_value(ret, key, value)
        else:
            ret = None

        if self.errors and not self._pending:
            raise ValidationError(
                self.errors,
                field_names=self.error_field_names,
                fields=self.error_fields,
                data=ret,
            )
        return ret

    # Make an instance callable
    __call__ = deserialize
