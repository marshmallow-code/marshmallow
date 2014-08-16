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
        def __init__(self, name, email, age=None):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()
            self.friends = []
            self.age = age

        def __repr__(self):
            return '<User(name={self.name!r})>'.format(self=self)


Create a serializer by defining a class with variables mapping attribute names to a field class object that formats the final output of the serializer.

.. code-block:: python

    from marshmallow import Serializer, fields, pprint

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()

For a full reference on the field classes, see the :ref:`API Docs <api_fields>`.


Serializing Objects
-------------------

Serialize objects by passing them to your serializer's :meth:`dump <marshmallow.Serializer.dump>` method, which returns the serialized ``result`` as a dictionary and a dictionary of validation errors.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    serializer = UserSerializer()
    result, errors = serializer.dump(user)
    pprint(result)
    # {'created_at': 'Sun, 10 Nov 2013 15:48:19 -0000',
    #  'email': u'monty@python.org',
    #  'name': u'Monty'}

.. note::

    Marshmallow provides a :func:`pprint` function for pretty-printing the ``OrderedDicts`` returned by the :meth:`dump <marshmallow.Serializer.dump>` method.

You can also serialize to a JSON-encoded string using :meth:`dumps <marshmallow.Serializer.dumps>`.

.. code-block:: python

    json_result, errors = serializer.dumps(user)
    pprint(json_result)
    # '{"created_at": "Sun, 10 Nov 2013 15:48:19 -0000", "name": "Monty", "email": "monty@python.org"}'

Filtering output
++++++++++++++++

You may not need to output all declared fields every time you use a serializer. You can specify which fields to output with the ``only`` parameter.

.. code-block:: python

    summary_serializer = UserSerializer(only=('name', 'email'))
    summary_serializer.dump(user)[0]
    # {"name": "Monty Python", "email": "monty@python.org"}

You can also exclude fields by passing in the ``exclude`` parameter.


Deserializing Objects
---------------------

The opposite of the :meth:`dump <Serializer.dump>` method is the :meth:`load <Serializer.load>` method, which deserializes an input dictionary to an application-level data structure (e.g. an ORM object in a web application).

By default, :meth:`load <Serializer.load>` will return a dictionary of field names mapped to the deserialized values.

.. code-block:: python

    from pprint import pprint

    user_data = {
        'created_at': '2014-08-11T05:26:03.869245',
        'email': u'ken@yahoo.com',
        'name': u'Ken'
    }
    serializer = UserSerializer()
    result, errors = serializer.load(user_data)
    pprint(result)
    # {'created_at': datetime.datetime(2014, 8, 11, 5, 26, 3, 869245),
    #  'email': 'ken@yahoo.com',
    #  'name': 'Ken'}

Notice that the datetime string was converted to a datetime object.

Deserializing to Objects
++++++++++++++++++++++++

In order to deserialize to an object, define the :meth:`make_object <Serializer.make_object>` method of your :class:`Serializer`. The method receives a dictionary of deserialized data as its only parameter.

.. code-block:: python

    # Same as above, but this time we define ``make_object``
    class UserSerializer(Serializer):

        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()

        def make_object(self, data):
            return User(**data)

Now, the :meth:`load <Serializer.load>` method will return a ``User`` object.

.. code-block:: python

    user_data = {
        'name': 'Ronnie',
        'email': 'ronnie@stones.com'
    }
    serializer = UserSerializer()
    result, errors = serializer.load(user_data)
    result  # => <User(name='Ronnie')>

Handling Collections of Objects
-------------------------------

Iterable collections of objects are also serializable and deserializable. Just set ``many=True``.

.. code-block:: python

    user1 = User(name="Mick", email="mick@stones.com")
    user2 = User(name="Keith", email="keith@stones.com")
    users = [user1, user2]
    serializer = UserSerializer(many=True)
    results, errors = serializer.dump(users)
    # [{'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'mick@stones.com',
    #   'name': u'Mick'},
    #  {'created_at': 'Fri, 08 Nov 2013 17:02:17 -0000',
    #   'email': u'keith@stones.com',
    #   'name': u'Keith'}]

Validation
----------

Both :meth:`Serializer.dump` and :meth:`Serializer.load` (as well as their JSON-encoding counterparts :meth:`Serializer.dumps` and :meth:`Serializer.loads`) return a dictionary of validation errors as the second element of their return value.

.. code-block:: python

    result, errors = UserSerializer().load({'email': 'foo'})
    errors  # => {'email': u'foo is not a valid email address.'}

You can give fields a custom error message by passing the ``error`` parameter to a field's constructor.

.. code-block:: python

    email = fields.Email(error='Invalid email address. Try again.')

You can perform additional validation for a field by passing it a ``validate`` callable (function, lambda, or object with ``__call__`` defined) which evaluates to a boolean.

.. code-block:: python

    class ValidatedUserSerializer(UserSerializer):
        age = fields.Number(validate=lambda n: 18 <= n <= 40,
                            error='User is over the hill')

    jagger = User(name="Mick", email="mick@stones.com", age=71)
    result, errors = ValidatedUserSerializer().dump(jagger)
    errors  # => {'age': 'User is over the hill'}

.. note::

    If you have multiple validations to perform, you may also pass a collection (list, tuple) or generator of callables to the ``validate`` parameter.

.. note::

    If you set ``strict=True`` in either the Serializer constructor or as a ``class Meta`` option, an error will be raised when invalid data are passed in.

    .. code-block:: python

        >>> UserSerializer(strict=True).dump(invalid)
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
          File "marshmallow/serializer.py", line 90, in __init__
            self.data = self.to_data()
          File "marshmallow/serializer.py", line 210, in to_data
            return self.marshal(self.obj, self.fields, *args, **kwargs)
          File "marshmallow/serializer.py", line 203, in marshal
            raise err
        MarshallingError: "foo" is not a valid email address.


    Alternatively, you can also register a custom error handler function for a serializer using the :func:`error_handler <Serializer.error_handler>` decorator. See the :ref:`Extending Serializers <extending>` page for more info.

Required Fields
+++++++++++++++

You can make a field required by passing ``required=True``. An error will be stored if the object's corresponding attribute is ``None``.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String(required=True)
        email = fields.Email()

    user = User(name=None, email='foo@bar.com')
    data, errors = UserSerializer().dump(user)
    errors  # {'name': 'Missing data for required field.'}


Specifying Attribute Names
--------------------------

By default, serializers will marshal the object attributes that have the same name as the fields. However, you may want to have different field and attribute names. In this case, you can explicitly specify which attribute names to use.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        email_addr = fields.String(attribute="email")
        date_created = fields.DateTime(attribute="created_at")

    user = User('Keith', email='keith@stones.com')
    ser = UserSerializer()
    result, errors = ser.dump(user)
    pprint(result)
    # {'email_addr': 'keith@stones.com',
    # 'date_created': 'Mon, 11 Aug 2014 01:53:16 -0000',
    # 'name': 'Keith'}

Refactoring (Meta Options)
--------------------------

When your model has many attributes, specifying the field type for every attribute can get repetitive, especially when many of the attributes are already native Python datatypes.

The *class Meta* paradigm allows you to specify which attributes you want to serialize. Marshmallow will choose an appropriate field type based on the attribute's type.

Let's refactor our User serializer to be more concise.

.. code-block:: python

    # Refactored serializer
    class UserSerializer(Serializer):
        uppername = fields.Function(lambda obj: obj.name.upper())
        class Meta:
            fields = ("name", "email", "created_at", "uppername")

Note that ``name`` will be automatically formatted as a :class:`String <marshmallow.fields.String>` and ``created_at`` will be formatted as a :class:`DateTime <marshmallow.fields.DateTime>`.

.. note::
    If instead you want to specify which field names to include *in addition* to the explicitly declared fields, you can use the ``additional`` option.

    The serializer below is equivalent to above:

    .. code-block:: python

        class UserSerializer(Serializer):
            uppername = fields.Function(lambda obj: obj.name.upper())
            class Meta:
                additional = ("name", "email", "created_at")  # No need to include 'uppername'

Nesting Serializers
-------------------

Serializers can be nested to represent relationships between objects (e.g. foreign key relationships). For example, a ``Blog`` may have an author represented by a User object.

.. code-block:: python

    # An example Blog model
    class Blog(object):
        def __init__(self, title, author):
            self.title = title
            self.author = author  # A User object

Use a :class:`Nested <marshmallow.fields.Nested>` field to represent the relationship, passing in the ``UserSerializer`` class.

.. code-block:: python

    class BlogSerializer(Serializer):
        title = fields.String()
        author = fields.Nested(UserSerializer)

When you serialize the blog, you will see the nested user representation.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    blog = Blog(title="Something Completely Different", author=user)
    result, errors = BlogSerializer().dump(blog)
    pprint(result)
    # {'author': {'created_at': 'Sun, 10 Nov 2013 16:10:57 -0000',
    #               'email': u'monty@python.org',
    #               'name': u'Monty'},
    #  'title': u'Something Completely Different'}

.. note::
    If the field is a collection of nested objects, you must set ``many=True``.

    .. code-block:: python

        collaborators = fields.Nested(UserSerializer, many=True)


Two-way Nesting
+++++++++++++++

If you have two objects that nest each other, you can refer to a nested serializer by its class name. This allows you to nest serializers that have not yet been defined.


For example, a representation of an ``Author`` model might include the books that have a foreign-key (many-to-one) relationship to it. Correspondingly, a representation of a ``Book`` will include its author representation.

.. code-block:: python

    class AuthorSerializer(Serializer):
        # Make sure to use the 'only' or 'exclude' params
        # to avoid infinite recursion
        books = fields.Nested('BookSerializer', many=True, exclude=('author', ))
        class Meta:
            fields = ('id', 'name', 'books')

    class BookSerializer(Serializer):
        author = fields.Nested('AuthorSerializer', only=('id', 'name'))
        class Meta:
            fields = ('id', 'title', 'author')

.. code-block:: python

    from marshmallow import pprint
    from mymodels import Author, Book

    author = Author(name='William Faulkner')
    book = Book(title='As I Lay Dying', author=author)
    book_result, errors = BookSerializer().dump(book)
    pprint(book_result, indent=2)
    # {
    #   "author": {
    #     "id": 8,
    #     "name": "William Faulkner"
    #   },
    #   "id": 124,
    #   "title": "As I Lay Dying"
    # }

    author_result, errors = AuthorSerializer().dump(author)
    pprint(author_result, indent=2)
    # {
    #   "books": [
    #     {
    #       "id": 124,
    #       "title": "As I Lay Dying"
    #     }
    #   ],
    #   "id": 8,
    #   "name": "William Faulkner"
    # }


Nesting A Serializer Within Itself
++++++++++++++++++++++++++++++++++

If the object to be serialized has a relationship to an object of the same type, you can nest the serializer within itself by passing ``"self"`` (with quotes) to the :class:`Nested <marshmallow.fields.Nested>` constructor.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.Email()
        friends = fields.Nested('self', many=True)

    user = User("Steve", 'steve@example.com')
    user.friends.append(User("Mike", 'mike@example.com'))
    user.friends.append(User('Joe', 'joe@example.com'))
    result, errors = UserSerializer().dump(user)
    pprint(result)
    # {
    #     "friends": [
    #         {"name": "Mike","email": "mike@example.com"},
    #         {"name": "Joe","email": "joe@example.com"},
    #     ],
    #     "name": "Steve",
    #     "email": "steve@example.com"
    # }

Specifying Nested Attributes
++++++++++++++++++++++++++++

You can explicitly specify which attributes in the nested fields you want to serialize with the ``only`` argument.

.. code-block:: python

    class BlogSerializer2(Serializer):
        title = fields.String()
        author = fields.Nested(UserSerializer, only=["email"])

    BlogSerializer2(blog).data
    # {
    #     'author': {'email': u'monty@python.org'},
    #     'title': u'Something Completely Different'
    # }

.. note::

    If you pass in a string field name to ``only``, only a single value (or flat list of values if ``many=True``) will be returned.

    .. code-block:: python

        class UserSerializer(Serializer):
            name = fields.String()
            email = fields.Email()
            friends = fields.Nested('self', only='name', many=True)
        # ... create ``user`` ...
        result, errors = UserSerializer().dump(user)
        pprint(result)
        # {
        #     "friends": ["Mike", "Joe"],
        #     "name": "Steve",
        #     "email": "steve@example.com"
        # }


You can also exclude fields by passing in an ``exclude`` list.


Custom Fields
-------------

There are three ways to create a custom-formatted field for a serializer:

- Create a custom field class
- Use a :class:`Method <marshmallow.fields.Method>` field
- Use a :class:`Function <marshmallow.fields.Function>` field

The method you choose will depend on personal preference and the manner in which you intend to reuse the field.

Creating A Field Class
++++++++++++++++++++++

To create a custom field class, create a subclass of :class:`marshmallow.fields.Raw <marshmallow.fields.Raw>` and implement its :meth:`_format <marshmallow.fields.Raw._format>`, :meth:`_serialize <marshmallow.fields.Raw._serialize>`, and/or :meth:`_deserialize <marshmallow.fields.Raw._deserialize>` methods.

.. code-block:: python

    from marshmallow import fields

    class Titlecased(fields.Raw):
        def _format(self, value):
            if value is None:
                return ''
            return value.title()

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        titlename = TitleCased(attribute="name")

Method Fields
+++++++++++++

A :class:`Method <marshmallow.fields.Method>` field will take the value returned by a method of the Serializer. The method must take an ``obj`` parameter which is the object to be serialized.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        since_created = fields.Method("get_days_since_created")

        def get_days_since_created(self, obj):
            return dt.datetime.now().day - obj.created_at.day

Function Fields
+++++++++++++++

A :class:`Function <marshmallow.fields.Function>` field will take the value of a function that is passed directly to it. Like a :class:`Method <marshmallow.fields.Method>` field, the function must take a single argument ``obj``.


.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        uppername = fields.Function(lambda obj: obj.name.upper())

Adding Context to Method and Function Fields
++++++++++++++++++++++++++++++++++++++++++++

New in version ``0.5.3``.

You may wish to include other objects when computing a :class:`Function <marshmallow.fields.Function>` or :class:`Method <marshmallow.fields.Method>` field.

As an example, you might want your ``UserSerializer`` to output whether or not a ``User`` is the author of a ``Blog``.

In these cases, you can pass a dictionary as the ``context`` argument to a serializer. :class:`Function <marshmallow.fields.Function>` and :class:`Method <marshmallow.fields.Method>` fields will have access to this dictionary.

.. code-block:: python

    class UserSerializer(Serializer):
        name = fields.String()
        is_author = fields.Function(lambda user, ctx: user == ctx['blog'].author)
        likes_bikes = fields.Method('writes_about_bikes')

        def writes_about_bikes(self, user, ctx):
            return 'bicycle' in ctx['blog'].title.lower()

    user = User('Freddie Mercury', 'fred@queen.com')
    blog = Blog('Bicycle Blog', author=user)

    context = {'blog': blog}
    result, errors = UserSerializer(context=context).dump(user)
    serialized.data['is_author']  # => True
    serialized.data['likes_bikes']  # => True


Next Steps
----------

Check out the :ref:`API Reference <api>` for a full listing of available fields.

Need to add custom post-processing or error handling behavior? See the :ref:`Extending Serializers <extending>` page.

For example applications using marshmallow, check out the :ref:`Examples <examples>` page.
