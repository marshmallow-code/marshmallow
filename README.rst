***********
marshmallow
***********

marshmallow is a Python library for converting complex datatypes, e.g. ORM/ODM objects, into native Python datatypes. The serialized objects can then be rendered to standard formats such as JSON for use in a REST API, for example.

Quickstart
==========

Declaring Serializers
---------------------

Let's start with basic "model".

.. code-block:: python

    import datetime as dt

    class User(object):
        def __init__(self, name, email):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()


Create a serializer by defining a class with a ``FIELDS`` variable, which is a dictionary mapping attribute names to a field class that formats the final output of the serializer.

.. code-block:: python

    from marshmallow import Serializer, fields

    class UserSerializer(Serializer):
        FIELDS = {
            "name": fields.String,
            'email': fields.String,
            'created_at': fields.DateTime
        }


Serializing Objects
-------------------

Serialize objects by passing them into your serializers. Onced serialized, you can get the dictionary representation via the `data` property and the JSON representation via the `json` property.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    serialized = UserSerializer(user)
    serialized.data
    # {'created_at': 'Sun, 10 Nov 2013 15:48:19 -0000',
    #  'email': u'monty@python.org',
    #  'name': u'Monty'}
    serialized.json
    # '{"created_at": "Sun, 10 Nov 2013 15:48:19 -0000", "name": "Monty", "email": "monty@python.org"}'


Specifying Attributes
---------------------

By default, serializers will marshal the object attributes that have the same name as the keys in ``FIELDS``. However, you may want to have different field and attribute names. In this case, you can explicitly specify which attribute names to use.

.. code-block:: python

    class UserSerializer(Serializer):
        FIELDS = {
            "name": fields.String,
            'email_addr': fields.String(attribute="email"),
            'date_created': fields.DateTime(attribute="created_at")
        }


Nesting Serializers
-------------------

Serializers can be nested to represent hierarchical structures. For example, a ``Blog`` may have an author represented by a User object.

.. code-block:: python

    class Blog(object):
        def __init__(self, title, author):
            self.title = title
            self.author = author  # A User object

Use ``fields.Nested``to represent relationship, passing in the ``UserSerializer`` class.

.. code-block:: python

    class BlogSerializer(Serializer):
        FIELDS = {
            'title': fields.String,
            'author': fields.Nested(UserSerializer)
        }

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
        FIELDS = {
            'title': fields.String,
            'author': fields.Nested(UserSerializer, only=["email"])
        }

    BlogSerializer2(blog).data
    # {'author': {'email': u'monty@python.org'}, 'title': u'Something Completely Different'}




Serializing Collections Objects
-------------------------------

You can serialize an iterable collection of objects.

.. code-block:: python

    user1 = User(name="Mick", email="mick@stones.com")
    user2 = User(name="Keith", email="keith@stones.com")
    users = [user1, user2]
    UserSerializer(users).data
    # [{'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'mick@stones.com',
    #   'name': u'Mick'},g
    #  {'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'keith@stones.com',
    #   'name': u'Keith'}]

Requirements
============

- Python >= 2.7 or >= 3.3


License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/marshmallow/blob/master/LICENSE>`_ file for more details.
