# -*- coding: utf-8 -*-
"""A registry of serializer classes. This allows for string lookup of
serializers, which may be used with
:class:`fields.Nested <marshmallow.fields.Nested>`.
"""
from marshmallow.exceptions import RegistryError


# {
#   <class_name>: <list of class objects>
# }
_registry = {}

def register(classname, cls):
    """Add a class to the registry of serializer classes."""
    if classname in _registry:
        _registry[classname].append(cls)
    else:
        _registry[classname] = [cls]
    return None

def get_class(classname):
    """Retrieve a class from the registry.

    :raises: marshmallow.exceptions.RegistryError if the class cannot be found
        or if there are multiple entries for the given class name.
    """
    try:
        classes = _registry[classname]
    except KeyError:
        raise RegistryError('Class with name {0!r} was not found. You may need '
            'to import the class.'.format(classname))
    if len(classes) > 1:
        raise RegistryError('Multiple classes with name {0!r} '
            'were found.'.format(classname))
    else:
        return _registry[classname][0]
