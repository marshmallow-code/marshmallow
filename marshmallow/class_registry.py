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
    # If the class is already registered; need to check if the entries are
    # in the same module as cls to avoid having multiple instances of the same
    # class in the registry
    if classname in _registry and not \
            any(each.__module__ == cls.__module__ for each in _registry[classname]):
        _registry[classname].append(cls)
    else:
        _registry[classname] = [cls]
    return None

def get_class(classname, all=False):
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
        if all:
            return _registry[classname]
        raise RegistryError('Multiple classes with name {0!r} '
            'were found.'.format(classname))
    else:
        return _registry[classname][0]
