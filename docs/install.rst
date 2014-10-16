.. _install:
.. module:: marshmallow

Installation
============

**marshmallow** requires Python >= 2.6 or >= 3.3. It has no external dependencies other than the Python standard library.

.. note::

    The `python-dateutil <http://labix.org/python-dateutil>`_ package is not a hard dependency, but it is recommended for robust datetime deserialization.

    ::

        $ pip install python-dateutil

Installing/Upgrading from the PyPI
----------------------------------

To install the latest version from the PyPI:

::

    $ pip install -U marshmallow

Get the Bleeding Edge Version
-----------------------------

To get the latest development version of marshmallow, run

::

    $ pip install -U git+https://github.com/sloria/marshmallow.git@dev

.. _migrating:

Migrating from Older Versions
-----------------------------

Migrating to 1.0
++++++++++++++++

Version 1.0 marks the first major release of marshmallow. Many big changes were made from the pre-1.0 releases in order to provide a cleaner API, support object deserialization, and improve field validation.

Perhaps the largest change is in how objects get serialized. Serialization occurs by invoking the :meth:`Schema.dump` method rather than passing the object to the constructor.  Because only configuration options (e.g. the ``many``, ``strict``, and ``only`` parameters) are passed to the constructor, you can more easily reuse serializer instances.  The :meth:`dump <Schema.dump>` method also forms a nice symmetry with the :meth:`Schema.load` method, which is used for deserialization.

.. code-block:: python

    class UserSchema(Schema):
        email = fields.Email()
        name = fields.String()

    user= User(email='monty@python.org', name='Monty Python')

    # 1.0
    serializer = UserSchema()
    data, errors = serializer.dump(user)
    # OR
    result = serializer.dump(user)
    result.data  # => serialized result
    result.errors  # => errors

    # Pre-1.0
    serialized = UserSchema(user)
    data = serialized.data
    errors = serialized.errors

.. module:: marshmallow.fields

The Fields interface was also reworked in 1.0 to make it easier to define custom fields with their own serialization and deserialization behavior. Custom fields now implement one or more of: :meth:`Field._serialize`, :meth:`Field._format`, and :meth:`Field._deserialize`.

.. code-block:: python

    from marshmallow import fields, MarshallingError

    class PasswordField(fields.Field):
        def _serialize(self, value, attr, obj):
            if not value or len(value) < 6:
                raise MarshallingError('Password must be greater than 6 characters.')
            return str(value).strip()

        # Similarly, you can override the _deserialize method


Another major change in 1.0 is that multiple validation errors can be stored for a single field. The ``errors`` dictionary returned by :meth:`Schema.dump` and :meth:`Schema.load` is a list of error messages keyed by field name.


.. code-block:: python

    from marshmallow import Schema, fields, ValidationError

    def must_have_number(val):
        if not any(ch.isdigit() for ch in val):
            raise ValidationError('Value must have an number.')

    def validate_length(val):
        if len(val) < 8:
            raise ValidationError('Value must have 8 or more characters.')

    class ValidatingSchema(Schema):
        password = fields.String(validate=[must_have_number, validate_length])

    result, errors = ValidatingSchema().load({'password': 'secure'})
    print(errors)
    # {'password': ['Value must have an number.',
    #               'Value must have 8 or more characters.']}

Other notable changes:

- :class:`Serializer` has been renamed to :class:`Schema`, but you can still import `marshmallow.Serializer`, which is just an alias for :class:`Schema`.
- ``datetime`` objects serialize to ISO8601 formatted strings by default (instead of RFC821 format).
- The ``fields.validated`` decorator was removed, as it is no longer necessary given the new Fields interface.
- `Schema.factory` class method was removed.
