.. _extending:
.. module:: marshmallow

Extending Serializers
=====================


Handling Errors
---------------

By default, a :class:`Serializer <Serializer>` will store its validation errors in a dictionary on the :func:`errors <Serializer.errors>` attribute (unless ``strict`` mode is enabled).

You can register a custom error-handling function for a :class:`Serializer <Serializer>` using the :func:`Serializer.error_handler <Serializer.error_handler>` decorator. The function receives the serializer instance, the errors dictionary, and the original object.


.. code-block:: python

    import logging

    class AppError(Exception):
        pass

    class UserSerializer(Serializer):
        email = fields.Email()

    @UserSerializer.error_handler
    def handle_errors(serializer, errors, obj):
        logging.error(errors)
        raise AppError('An error occurred while serializing {0}'.format(obj))


    invalid = User('Foo Bar', email='foo')
    s = UserSerializer(invalid)  # raises AppError


Transforming Data
-----------------

The :func:`Serializer.data_handler <Serializer.data_handler>` decorator can be used to register data post-processing functions that transform the serialized data.

One use case might be to add a "root" namespace for a serialized object.
