===========
marshmallow
===========

Serialization made simple.

.. code:: python

    from marshmallow import Serializer, fields

    class User(object):
        def __init__(self, name, email):
            self.name = name
            self.email = email

    class UserSerializer(Serializer):
        FIELDS = {
            "name": fields.String,
            "email": fields.String
        }


.. code:: python

    >>> user = User(name="Monty Python", email="monty@python.org")
    >>> serialized = UserSerializer(user)
    >>> serialized.data
    {"name": "Monty Python", "email": "monty@python.org"}



Requirements
------------

- Python >= 2.6 or >= 3.3


License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/marshmallow/blob/master/LICENSE>`_ file for more details.
