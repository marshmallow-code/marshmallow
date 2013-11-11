.. _quickstart:
.. module:: marshmallow

Quickstart
==========

This guide will walk you through the basics of creating an object serializer.

Declaring Serializers
---------------------

Let's start with a basic user model.

.. code-block:: python

    import datetime as dt

    class User(object):
        def __init__(self, name, email):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()


Create a serializer by defining a class with variables mapping attribute names to a field class object that formats the final output of the serializer.

.. code-block:: python

    from marshmallow import Serializer, fields

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()

For a full reference on the field classes, see the :ref:`API Docs <api_fields>`.


Serializing Objects
-------------------

Serialize objects by passing them into your serializers. Onced serialized, you can get the dictionary representation via the ``data`` property and the JSON representation via the ``json`` property.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    serialized = UserSerializer(user)
    serialized.data
    # {'created_at': 'Sun, 10 Nov 2013 15:48:19 -0000',
    #  'email': u'monty@python.org',
    #  'name': u'Monty'}
    serialized.json
    # '{"created_at": "Sun, 10 Nov 2013 15:48:19 -0000", "name": "Monty", "email": "monty@python.org"}'

Validation
----------

To validate the data passed to a serializer, call the ``is_valid()`` method.

.. code-block:: python

    invalid = User("Foo Bar", email="foo")
    s = UserSerializer(invalid)
    s.is_valid()
    # False

You can get a dictionary of validation errors via the ``errors`` property.

.. code-block:: python

    s.errors
    # {'email': u'foo is not a valid email address.'}


Specifying Attribute Names
--------------------------

By default, serializers will marshal the object attributes that have the same name as the fields. However, you may want to have different field and attribute names. In this case, you can explicitly specify which attribute names to use.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        email_addr = fields.String(attribute="email")
        date_created = fields.DateTime(attribute="created_at")


Nesting Serializers
-------------------

Serializers can be nested to represent hierarchical structures. For example, a ``Blog`` may have an author represented by a User object.

.. code-block:: python

    class Blog(object):
        def __init__(self, title, author):
            self.title = title
            self.author = author  # A User object

Use ``fields.Nested`` to represent the relationship, passing in the ``UserSerializer`` class.

.. code-block:: python

    class BlogSerializer(Serializer):
        title = fields.String()
        author = fields.Nested(UserSerializer)

When you serialize the blog, you will see the nested user representation.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    blog = Blog(title="Something Completely Different", author=user)
    serialized = BlogSerializer(blog)
    serialized.data
    # {'author': {'created_at': 'Sun, 10 Nov 2013 16:10:57 -0000',
    #   'email': u'monty@python.org',
    #   'name': u'Monty'},
    #  'title': u'Something Completely Different'}

Specifying Nested Attributes
++++++++++++++++++++++++++++

You can explicitly specify which attributes in the nested fields you want to serialize in the ``only`` argument.

.. code-block:: python

    class BlogSerializer2(Serializer):
        title = fields.String()
        author = fields.Nested(UserSerializer, only=["email"])

    BlogSerializer2(blog).data
    # {'author': {'email': u'monty@python.org'}, 'title': u'Something Completely Different'}

You can also exclude fields by passing in an ``exclude`` list.


Serializing Collections of Objects
----------------------------------

Iterable collections of objects are also serializable.

.. code-block:: python

    user1 = User(name="Mick", email="mick@stones.com")
    user2 = User(name="Keith", email="keith@stones.com")
    users = [user1, user2]
    UserSerializer(users).data
    # [{'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'mick@stones.com',
    #   'name': u'Mick'},
    #  {'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'keith@stones.com',
    #   'name': u'Keith'}]

Creating Custom Fields
----------------------

To create custom formatted fields, create a subclass of :class:`marshmallow.fields.Raw <marshmallow.fields.Raw>` and implement its ``format`` and or ``output`` methods.

.. code-block:: python

    from marshmallow import fields

    class Uppercased(fields.Raw):
        def format(self, value):
            return value.upper()

Printing Serialized Data
------------------------

Marshmallow provides a ``pprint`` function for pretty-printing the OrderedDicts returned by ``Serializer.data``.

.. code-block:: python

    >>> from marshmallow import pprint
    >>> u = User("Monty Python", email="monty@python.org")
    >>> serialized = UserSerializer(u)
    >>> pprint(serialized.data, indent=4)
    {
        "created_at": "Sun, 10 Nov 2013 20:31:36 -0000",
        "name": "Monty Python",
        "email": "monty@python.org"
    }
