# -*- coding: utf-8 -*-
"""A registry of serializer classes. This allows for string lookup of
serializers, which may be used with
:class:`fields.Nested <marshmallow.fields.Nested>`.
"""

# {
#   <class_name>: <list of class objects>
# }
_registry = {}

def register(classname, cls):
    """Add a class to the registry of serializer classes."""
    if classname in _registry:
        existing = _registry[classname]
        _registry[classname] = [existing, cls]
    else:
        _registry[classname] = [cls]
    return None

def get_class(classname):
    try:
        classes = _registry[classname]
    except KeyError:
        raise RuntimeError('Class with name {0!r} was not found. You may need '
            'to import the class.')
    if len(classes) > 1:
        raise RuntimeError('Multiple classes with name {0!r} '
            'were found.'.format(classname))
    else:
        return _registry[classname][0]
