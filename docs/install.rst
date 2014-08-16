.. _install:
.. module:: marshmallow

Installation
============

**marshmallow** requires Python >= 2.6 or >= 3.3. It has no external dependencies other than the Python standard library.

.. note::

    The ``python-dateutil`` package is not a hard dependency, but it is recommended for robust datetime deserialization.

    ::

        $ pip install python-dateutil

From the PyPI
-------------

To install the latest version from the PyPI:

::

    $ pip install -U marshmallow

From Source
-----------

Alternatively, you can install marshmallow from source.

You can clone the public repo: ::

    $ git clone https://github.com/sloria/marshmallow.git

Or download one of the following:

* tarball_
* zipball_

Once you have the source, you can install it into your site-packages with ::

    $ python setup.py install

.. _Github: https://github.com/sloria/marshmallow
.. _tarball: https://github.com/sloria/marshmallow/tarball/master
.. _zipball: https://github.com/sloria/marshmallow/zipball/master


Migrating from Older Versions
-----------------------------

Migrating to 1.0.0
++++++++++++++++++

Version 1.0.0 marks the first major release of marshmallow. Many big changes were made from the pre-1.0 releases in order to provide a cleaner, more flexible API and also to support object deserialization.

Perhaps the largest change is in how objects get serialized. Serialization occurs by invoking the :meth:`Serializer.dump` method rather than passing the object to the constructor.  Because only configuration options (e.g. the ``many``, ``strict``, and ``only`` parameters) are passed to the constructor, you can more easily reuse serializer instances.  The :meth:`dump <Serializer.dump>` method also forms a nice symmetry with the :meth:`Serializer.load` method, which is used for deserialization.

.. code-block:: python

    class UserSerializer(Serializer):
        email = fields.Email()
        name = fields.String()

    user= User(email='monty@python.org', name='Monty Python')

    # 1.0
    serializer = UserSerializer()
    data, errors = serializer.dump(user)

    # Pre-1.0
    serialized = UserSerializer(user)
    data = serialized.data
    errors = serialized.errors

The Fields interface was also reworked in 1.0.0 to make it easier to define custom fields with their own serialization and deserialization behavior.

.. code-block:: python

    from marshmallow import fields, MarshallingError

    class PasswordField(fields.Field):
        def _serialize(self, value, attr, obj):
            if not value or len(value) < 6:
                raise MarshallingError('Password must be greater than 6 characters.')
            return str(value).strip()

        # Similarly, you can override the _deserialize method

Other notable changes:

- ``datetime`` objects serialize to ISO8601 formatted strings by default (instead of RFC821 format), as in pre-1.0 releases
- The ``fields.validated`` decorator was removed, as it is no longer necessary given the new Fields interface.
