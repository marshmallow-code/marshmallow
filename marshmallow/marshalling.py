# -*- coding: utf-8 -*-
"""Utility classes and values used for marshalling and unmarshalling objects to
and from primitive types.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import unicode_literals

from marshmallow import base, utils
from marshmallow.compat import text_type, iteritems
from marshmallow.exceptions import (
    ValidationError,
    MarshallingError,
)

__all__ = [
    'Marshaller',
    'Unmarshaller',
    'null',
    'missing',
]

class _Null(object):

    def __bool__(self):
        return False

    __nonzero__ = __bool__  # PY2 compat

    def __repr__(self):
        return '<marshmallow.marshalling.null>'


class _Missing(_Null):

    def __repr__(self):
        return '<marshmallow.marshalling.missing>'


# Singleton that represents an empty value. Used as the default for Nested
# fields so that `Field._call_with_validation` is invoked, even when the
# object to serialize has the nested attribute set to None. Therefore,
# `RegistryErrors` are properly raised.
null = _Null()

# Singleton value that indicates that a field's value is missing from input
# dict passed to :meth:`Schema.load`. If the field's value is not required,
# it's ``default`` value is used.
missing = _Missing()


def _call_and_store(getter_func, data, field_name, field_obj, errors_dict,
               exception_class, strict=False, index=None):
    """Helper method for DRYing up logic in the :meth:`Marshaller.serialize` and
    :meth:`Unmarshaller.deserialize` methods. Call ``getter_func`` with ``data`` as its
    argument, and store any errors of type ``exception_class`` in ``error_dict``.

    :param callable getter_func: Function for getting the serialized/deserialized
        value from ``data``.
    :param data: The data passed to ``getter_func``.
    :param str field_name: Field name.
    :param FieldABC field_obj: Field object that performs the
        serialization/deserialization behavior.
    :param dict errors_dict: Dictionary to store errors on.
    :param type exception_class: Exception class that will be caught during
        serialization/deserialization. Errors of this type will be stored
        in ``errors_dict``.
    :param int index: Index of the item being validated, if validating a collection,
        otherwise `None`.
    """
    try:
        value = getter_func(data)
    except exception_class as err:  # Store errors
        if strict:
            err.field = field_obj
            err.field_name = field_name
            raise err
        # Warning: Mutation!
        if index is not None:
            errors = {}
            errors_dict[index] = errors
        else:
            errors = errors_dict
        # Warning: Mutation!
        if isinstance(err, ValidationError):
            if isinstance(err.messages, dict):
                errors[field_name] = err.messages
            else:
                errors.setdefault(field_name, []).extend(err.messages)
        else:
            errors.setdefault(field_name, []).append(text_type(err))
        value = None
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


class Marshaller(object):
    """Callable class responsible for serializing data and storing errors.

    :param str prefix: Optional prefix that will be prepended to all the
        serialized field names.
    """
    def __init__(self, prefix=''):
        self.prefix = prefix
        #: Dictionary of errors stored during serialization
        self.errors = {}
        #: True while serializing a collection
        self.__pending = False

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
        if not self.__pending:
            self.errors = {}
        if many and obj is not None:
            self.__pending = True
            ret = [self.serialize(d, fields_dict, many=False, strict=strict,
                                    dict_class=dict_class, accessor=accessor,
                                    skip_missing=skip_missing,
                                    index=idx, index_errors=index_errors)
                    for idx, d in enumerate(obj)]
            self.__pending = False
            return ret
        items = []
        for attr_name, field_obj in iteritems(fields_dict):
            key = ''.join([self.prefix, attr_name])
            getter = lambda d: field_obj.serialize(attr_name, d, accessor=accessor)
            value = _call_and_store(
                getter_func=getter,
                data=obj,
                field_name=key,
                field_obj=field_obj,
                errors_dict=self.errors,
                exception_class=MarshallingError,
                strict=strict,
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
        return dict_class(items)

    # Make an instance callable
    __call__ = serialize


class Unmarshaller(object):
    """Callable class responsible for deserializing data and storing errors.

    .. versionadded:: 1.0.0
    """
    def __init__(self):
        #: Dictionary of errors stored during deserialization
        self.errors = {}
        #: True while deserializing a collection
        self.__pending = False

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
                if err.fields:
                    field_names = err.fields
                    field_objs = [fields_dict[each] for each in field_names]
                else:
                    field_names = ['_schema']
                    field_objs = []
                if strict:
                    raise ValidationError(
                        err.messages,
                        fields=field_objs,
                        field_names=field_names
                    )
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
        if not self.__pending:
            self.errors = {}
        if many and data is not None:
            self.__pending = True
            ret = [self.deserialize(d, fields_dict, many=False,
                        validators=validators, preprocess=preprocess,
                        postprocess=postprocess, strict=strict, dict_class=dict_class,
                        index=idx, index_errors=index_errors)
                    for idx, d in enumerate(data)]
            self.__pending = False
            return ret
        raw_data = data
        if data is not None:
            items = []
            for attr_name, field_obj in iteritems(fields_dict):
                if field_obj.dump_only:
                    continue
                key = fields_dict[attr_name].attribute or attr_name
                raw_value = data.get(attr_name, missing)
                if raw_value is missing and field_obj.load_from:
                    raw_value = data.get(field_obj.load_from, missing)
                if raw_value is missing and field_obj.missing is not null:
                    _miss = field_obj.missing
                    raw_value = _miss() if callable(_miss) else _miss
                if raw_value is missing and not field_obj.required:
                    continue
                value = _call_and_store(
                    getter_func=field_obj.deserialize,
                    data=raw_value,
                    field_name=key,
                    field_obj=field_obj,
                    errors_dict=self.errors,
                    exception_class=ValidationError,
                    strict=strict,
                    index=(index if index_errors else None)
                )
                if raw_value is not missing:
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
        if postprocess:
            postprocess = postprocess or []
            for func in postprocess:
                ret = func(ret)
        return ret

    # Make an instance callable
    __call__ = deserialize
