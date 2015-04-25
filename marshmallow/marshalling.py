# -*- coding: utf-8 -*-
"""Utility classes and values used for marshalling and unmarshalling objects to
and from primitive types.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals

from marshmallow import base, utils
from marshmallow.utils import missing
from marshmallow.compat import text_type, iteritems
from marshmallow.exceptions import (
    ValidationError,
)

__all__ = [
    'Marshaller',
    'Unmarshaller',
]


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

    def reset_errors(self):
        self.errors = {}
        self.error_field_names = []
        self.error_fields = []

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
            self.error_fields.append(field_obj)
            self.error_field_names.append(field_name)
            if index is not None:
                errors = self.errors.get(index, {})
                self.errors[index] = errors
            else:
                errors = self.errors
            # Warning: Mutation!
            if isinstance(err.messages, dict):
                errors[field_name] = err.messages
            else:
                errors.setdefault(field_name, []).extend(err.messages)
            value = missing
        except TypeError:
            # field declared as a class, not an instance
            if (isinstance(field_obj, type) and
                    issubclass(field_obj, base.FieldABC)):
                msg = ('Field for "{0}" must be declared as a '
                                'Field instance, not a class. '
                                'Did you mean "fields.{1}()"?'
                                .format(field_name, field_obj.__name__))
                raise TypeError(msg)
            raise
        return value

class Marshaller(ErrorStore):
    """Callable class responsible for serializing data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    """
    def __init__(self, prefix=''):
        self.prefix = prefix
        ErrorStore.__init__(self)

    def serialize(self, obj, fields_dict, many=False, strict=False, skip_missing=False,
                  accessor=None, dict_class=dict, index_errors=True, index=None):
        """Takes raw data (a dict, list, or other object) and a dict of
        fields to output and serializes the data based on those fields.

        :param obj: The actual object(s) from which the fields are taken from
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be serialized as
            a collection.
        :param bool strict: If `True`, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :param skip_missing: If `True`, skip key:value pairs when ``value`` is `None`.
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
        # Reset errors dict if not serializing a collection
        if not self._pending:
            self.reset_errors()
        if many and obj is not None:
            self._pending = True
            ret = [self.serialize(d, fields_dict, many=False, strict=strict,
                                    dict_class=dict_class, accessor=accessor,
                                    skip_missing=skip_missing,
                                    index=idx, index_errors=index_errors)
                    for idx, d in enumerate(obj)]
            self._pending = False
            return ret
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = ''.join([self.prefix, attr_name])
            getter = lambda d: field_obj.serialize(attr_name, d, accessor=accessor)
            value = self.call_and_store(
                getter_func=getter,
                data=obj,
                field_name=key,
                field_obj=field_obj,
                index=(index if index_errors else None)
            )
            skip_conds = (
                field_obj.load_only,
                value is missing,
                skip_missing and value in field_obj.SKIPPABLE_VALUES,
            )
            if any(skip_conds):
                continue
            items.append((key, value))
        if self.errors and strict:
            raise ValidationError(
                self.errors,
                field_names=self.error_field_names,
                fields=self.error_fields
            )
        return dict_class(items)

    # Make an instance callable
    __call__ = serialize


class Unmarshaller(ErrorStore):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """

    def _validate(self, validators, output, raw_data, fields_dict, strict=False):
        """Perform schema-level validation. Stores errors if ``strict`` is `False`.
        """
        for validator_func in validators:
            try:
                func_args = utils.get_func_args(validator_func)
                if len(func_args) < 3:
                    res = validator_func(output)
                else:
                    res = validator_func(output, raw_data)
                if res is False:
                    func_name = utils.get_func_name(validator_func)
                    raise ValidationError('Schema validator {0}({1}) is False'.format(
                        func_name, dict(output)
                    ))
            except ValidationError as err:
                # Store or reraise errors
                if err.field_names:
                    field_names = err.field_names
                    field_objs = [fields_dict[each] for each in field_names]
                else:
                    field_names = ['_schema']
                    field_objs = []
                for field_name in field_names:
                    if isinstance(err.messages, (list, tuple)):
                        # self.errors[field_name] may be a dict if schemas are nested
                        if isinstance(self.errors.get(field_name), dict):
                            self.errors[field_name].setdefault(
                                '_schema', []
                            ).extend(err.messages)
                        else:
                            self.errors.setdefault(field_name, []).extend(err.messages)
                    elif isinstance(err.messages, dict):
                        self.errors.setdefault(field_name, []).append(err.messages)
                    else:
                        self.errors.setdefault(field_name, []).append(text_type(err))
                if strict:
                    raise ValidationError(
                        self.errors,
                        fields=field_objs,
                        field_names=field_names
                    )
        return output

    def deserialize(self, data, fields_dict, many=False, validators=None,
            preprocess=None, postprocess=None, strict=False, dict_class=dict,
            index_errors=True, index=None):
        """Deserialize ``data`` based on the schema defined by ``fields_dict``.

        :param dict data: The data to deserialize.
        :param dict fields_dict: Mapping of field names to :class:`Field` objects.
        :param bool many: Set to `True` if ``data`` should be deserialized as
            a collection.
        :param list validators: List of validation functions to apply to the
            deserialized dictionary.
        :param list preprocess: List of pre-processing functions.
        :param list postprocess: List of post-processing functions.
        :param bool strict: If `True`, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :param type dict_class: Dictionary class used to construct the output.
        :param bool index_errors: Whether to store the index of invalid items in
            ``self.errors`` when ``many=True``.
        :param int index: Index of the item being serialized (for storing errors) if
            serializing a collection, otherwise `None`.
        :return: A dictionary of the deserialized data.
        """
        # Reset errors if not deserializing a collection
        if not self._pending:
            self.reset_errors()
        if many and data is not None:
            self._pending = True
            ret = [self.deserialize(d, fields_dict, many=False,
                        validators=validators, preprocess=preprocess,
                        postprocess=postprocess, strict=strict, dict_class=dict_class,
                        index=idx, index_errors=index_errors)
                    for idx, d in enumerate(data)]
            self._pending = False
            return ret
        raw_data = data
        if data is not None:
            items = []
            for attr_name, field_obj in iteritems(fields_dict):
                if field_obj.dump_only:
                    continue
                key = fields_dict[attr_name].attribute or attr_name
                try:
                    raw_value = data.get(attr_name, missing)
                except AttributeError:
                    msg = 'Data must be a dict, got a {0}'.format(data.__class__.__name__)
                    raise ValidationError(
                        msg,
                        field_names=[attr_name],
                        fields=[field_obj]
                    )
                if raw_value is missing and field_obj.load_from:
                    raw_value = data.get(field_obj.load_from, missing)
                if raw_value is missing:
                    _miss = field_obj.missing
                    raw_value = _miss() if callable(_miss) else _miss
                if raw_value is missing and not field_obj.required:
                    continue
                value = self.call_and_store(
                    getter_func=field_obj.deserialize,
                    data=raw_value,
                    field_name=key,
                    field_obj=field_obj,
                    index=(index if index_errors else None)
                )
                if value is not missing:
                    items.append((key, value))
            ret = dict_class(items)
        else:
            ret = None

        if preprocess:
            preprocess = preprocess or []
            for func in preprocess:
                ret = func(ret)
        if validators:
            validators = validators or []
            ret = self._validate(validators, ret, raw_data, fields_dict=fields_dict,
                                 strict=strict)
        if self.errors and strict:
            raise ValidationError(
                self.errors,
                field_names=self.error_field_names,
                fields=self.error_fields
            )
        if postprocess:
            postprocess = postprocess or []
            for func in postprocess:
                ret = func(ret)
        return ret

    # Make an instance callable
    __call__ = deserialize
