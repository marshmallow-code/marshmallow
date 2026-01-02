"""Utilities for storing collections of error messages.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from marshmallow.exceptions import SCHEMA


class ErrorStore:
    def __init__(self):
        #: Dictionary of errors stored during serialization
        self.errors = {}

    def store_error(self, messages, field_name=SCHEMA, index=None):
        # field error  -> store/merge error messages under field name key
        # schema error -> if string or list, store/merge under _schema key
        #              -> if dict, store/merge with other top-level keys
        messages = copy_containers(messages)
        if field_name != SCHEMA or not isinstance(messages, dict):
            messages = {field_name: messages}
        if index is not None:
            messages = {index: messages}
        self.errors = merge_errors(self.errors, messages)


def copy_containers(errors):
    if isinstance(errors, list):
        return [copy_containers(val) for val in errors]
    if isinstance(errors, dict):
        return {key: copy_containers(val) for key, val in errors.items()}
    return errors


def merge_errors(errors1, errors2):  # noqa: PLR0911
    """Deeply merge two error messages.

    The format of ``errors1`` and ``errors2`` matches the ``message``
    parameter of :exc:`marshmallow.exceptions.ValidationError`.
    """
    if not errors1:
        return errors2
    if not errors2:
        return errors1
    if isinstance(errors1, list):
        if isinstance(errors2, list):
            errors1.extend(errors2)
            return errors1
        if isinstance(errors2, dict):
            errors2[SCHEMA] = merge_errors(errors1, errors2.get(SCHEMA))
            return errors2
        errors1.append(errors2)
        return errors1
    if isinstance(errors1, dict):
        if isinstance(errors2, dict):
            for key, val in errors2.items():
                if key in errors1:
                    errors1[key] = merge_errors(errors1[key], val)
                else:
                    errors1[key] = val
            return errors1
        errors1[SCHEMA] = merge_errors(errors1.get(SCHEMA), errors2)
        return errors1
    if isinstance(errors2, list):
        return [errors1, *errors2]
    if isinstance(errors2, dict):
        errors2[SCHEMA] = merge_errors(errors1, errors2.get(SCHEMA))
        return errors2
    return [errors1, errors2]
