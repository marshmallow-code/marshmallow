.. _quickstart:
.. module:: marshmallow

Quickstart
==========

This guide will walk you through the basics of creating schemas for serializing and deserializing data.

Declaring Schemas
-----------------

Let's start with a basic user model.

.. code-block:: python

    import datetime as dt

    class User(object):
        def __init__(self, name, email, age=None):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()
            self.friends = []
            self.employer = None
            self.age = age

        def __repr__(self):
            return '<User(name={self.name!r})>'.format(self=self)


Create a schema by defining a class with variables mapping attribute names to a :class:`Field <fields.Field>` objects.

.. code-block:: python

    from marshmallow import Schema, fields, pprint

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()

.. seealso::

    For a full reference on the available field classes, see the :ref:`API Docs <api_fields>`.


Serializing Objects
-------------------

Serialize objects by passing them to your schema's :meth:`dump <marshmallow.Schema.dump>` method, which returns the formatted result (as well as a dictionary of validation errors, which we'll revisit later).

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    schema = UserSchema()
    result = schema.dump(user)
    pprint(result.data)
    # {"name": "Monty",
    #  "email": "monty@python.org",
    #  "created_at": "2014-08-17T14:54:16.049594+00:00"}

.. note::

    Marshmallow provides a :func:`pprint` function for pretty-printing the ``OrderedDicts`` returned by the :meth:`dump <marshmallow.Schema.dump>` method.

You can also serialize to a JSON-encoded string using :meth:`dumps <marshmallow.Schema.dumps>`.

.. code-block:: python

    json_result = schema.dumps(user)
    pprint(json_result.data)
    # '{"name": "Monty", "email": "monty@python.org", "created_at": "2014-08-17T14:54:16.049594+00:00"}'

Filtering output
++++++++++++++++

You may not need to output all declared fields every time you use a schema. You can specify which fields to output with the ``only`` parameter.

.. code-block:: python

    summary_schema = UserSchema(only=('name', 'email'))
    summary_schema.dump(user).data
    # {"name": "Monty Python", "email": "monty@python.org"}

You can also exclude fields by passing in the ``exclude`` parameter.


Deserializing Objects
---------------------

The opposite of the :meth:`dump <Schema.dump>` method is the :meth:`load <Schema.load>` method, which deserializes an input dictionary to an application-level data structure (e.g. an ORM object in a web application).

By default, :meth:`load <Schema.load>` will return a dictionary of field names mapped to the deserialized values.

.. code-block:: python

    from pprint import pprint

    user_data = {
        'created_at': '2014-08-11T05:26:03.869245',
        'email': u'ken@yahoo.com',
        'name': u'Ken'
    }
    schema = UserSchema()
    result = schema.load(user_data)
    pprint(result.data)
    # {'name': 'Ken',
    #  'email': 'ken@yahoo.com',
    #  'created_at': datetime.datetime(2014, 8, 11, 5, 26, 3, 869245)},

Notice that the datetime string was converted to a datetime object.

Deserializing to Objects
++++++++++++++++++++++++

In order to deserialize to an object, define the :meth:`make_object <Schema.make_object>` method of your :class:`Schema`. The method receives a dictionary of deserialized data as its only parameter.

.. code-block:: python

    # Same as above, but this time we define ``make_object``
    class UserSchema(Schema):

        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()

        def make_object(self, data):
            return User(**data)

Now, the :meth:`load <Schema.load>` method will return a ``User`` object.

.. code-block:: python

    user_data = {
        'name': 'Ronnie',
        'email': 'ronnie@stones.com'
    }
    schema = UserSchema()
    result = schema.load(user_data)
    result.data  # => <User(name='Ronnie')>

Handling Collections of Objects
-------------------------------

Iterable collections of objects are also serializable and deserializable. Just set ``many=True``.

.. code-block:: python

    user1 = User(name="Mick", email="mick@stones.com")
    user2 = User(name="Keith", email="keith@stones.com")
    users = [user1, user2]
    schema = UserSchema(many=True)
    result = schema.dump(users)
    result.data
    # [{'name': u'Mick',
    #   'email': u'mick@stones.com',
    #   'created_at': '2014-08-17T14:58:57.600623+00:00'}
    #  {'name': u'Keith',
    #   'email': u'keith@stones.com',
    #   'created_at': '2014-08-17T14:58:57.600623+00:00'}]

Validation
----------

:meth:`Schema.load` (and its JSON-encoding counterpart, :meth:`Schema.loads`) returns a dictionary of validation errors as the second element of its return value.

.. code-block:: python

    result, errors = UserSchema().load({'email': 'foo'})
    errors  # => {'email': ['foo is not a valid email address.']}

You can perform additional validation for a field by passing it a ``validate`` callable (function, lambda, or object with ``__call__`` defined).

.. code-block:: python

    class ValidatedUserSchema(UserSchema):
        age = fields.Number(validate=lambda n: 18 <= n <= 40)

    in_data = {'name': 'Mick', 'email': 'mick@stones.com', 'age': 71}
    result, errors = ValidatedUserSchema().load(in_data)
    errors  # => {'age': ['Validator <lambda>(71.0) is False']}


Validation functions either return a boolean or raise a :exc:`ValidationError`. If a :exc:`ValidationError` is raised, its message is stored when validation fails.

.. code-block:: python

    from marshmallow import Schema, fields, ValidationError

    def validate_quantity(n):
        if n < 0:
            raise ValidationError('Quantity must be greater than 0.')
        if n > 30:
            raise ValidationError('Quantity must not be greater than 30.')

    class ItemSchema(Schema):
        quantity = fields.Integer(validate=validate_quantity)

    in_data = {'quantity': 31}
    result, errors = ItemSchema().load(in_data)
    errors  # => {'quantity': ['Quantity must not be greater than 30.']}

.. note::

    If you have multiple validations to perform, you may also pass a collection (list, tuple) or generator of callables to the ``validate`` parameter.

.. note::

    :meth:`Schema.dump` also validates the format of its fields and returns a dictionary of errors. However, the callables passed to ``validate`` are only applied during deserialization.

.. note::

    If you set ``strict=True`` in either the Schema constructor or as a ``class Meta`` option, an error will be raised when invalid data are passed in.

    .. code-block:: python

        UserSchema(strict=True).load({'email': 'foo'})
        # => UnmarshallingError: "foo" is not a valid email address.


    Alternatively, you can also register a custom error handler function for a schema using the :func:`error_handler <Schema.error_handler>` decorator. See the :ref:`Extending Schemas <extending>` page for more info.


.. seealso::

    Need schema-level validation? See the :ref:`Extending Schemas <schemavalidation>` page.

Required Fields
+++++++++++++++

You can make a field required by passing ``required=True``. An error will be stored if the the value is missing from the input to :meth:`Schema.load`.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String(required=True)
        email = fields.Email()

    data, errors = UserSchema().load({'email': 'foo@bar.com'})
    errors  # {'name': ['Missing data for required field.']}


Specifying Attribute Names
--------------------------

By default, `Schemas` will marshal the object attributes that have the same name as the fields. However, you may want to have different field and attribute names. In this case, you can explicitly specify which attribute names to use.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email_addr = fields.String(attribute="email")
        date_created = fields.DateTime(attribute="created_at")

    user = User('Keith', email='keith@stones.com')
    ser = UserSchema()
    result, errors = ser.dump(user)
    pprint(result)
    # {'name': 'Keith',
    #  'email_addr': 'keith@stones.com',
    #  'date_created': '2014-08-17T14:58:57.600623+00:00'}


.. _meta_options:

Refactoring (Meta Options)
--------------------------

When your model has many attributes, specifying the field type for every attribute can get repetitive, especially when many of the attributes are already native Python datatypes.

The *class Meta* paradigm allows you to specify which attributes you want to serialize. Marshmallow will choose an appropriate field type based on the attribute's type.

Let's refactor our User schema to be more concise.

.. code-block:: python

    # Refactored schema
    class UserSchema(Schema):
        uppername = fields.Function(lambda obj: obj.name.upper())
        class Meta:
            fields = ("name", "email", "created_at", "uppername")

Note that ``name`` will be automatically formatted as a :class:`String <marshmallow.fields.String>` and ``created_at`` will be formatted as a :class:`DateTime <marshmallow.fields.DateTime>`.

.. note::
    If instead you want to specify which field names to include *in addition* to the explicitly declared fields, you can use the ``additional`` option.

    The schema below is equivalent to above:

    .. code-block:: python

        class UserSchema(Schema):
            uppername = fields.Function(lambda obj: obj.name.upper())
            class Meta:
                additional = ("name", "email", "created_at")  # No need to include 'uppername'

Nesting Schemas
---------------

Schemas can be nested to represent relationships between objects (e.g. foreign key relationships). For example, a ``Blog`` may have an author represented by a User object.

.. code-block:: python

    # An example Blog model
    class Blog(object):
        def __init__(self, title, author):
            self.title = title
            self.author = author  # A User object

Use a :class:`Nested <marshmallow.fields.Nested>` field to represent the relationship, passing in the ``UserSchema`` class.

.. code-block:: python

    class BlogSchema(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema)

When you serialize the blog, you will see the nested user representation.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    blog = Blog(title="Something Completely Different", author=user)
    result, errors = BlogSchema().dump(blog)
    pprint(result)
    # {'title': u'Something Completely Different',
    # {'author': {'name': u'Monty',
    #             'email': u'monty@python.org',
    #             'created_at': '2014-08-17T14:58:57.600623+00:00'}}

.. note::
    If the field is a collection of nested objects, you must set ``many=True``.

    .. code-block:: python

        collaborators = fields.Nested(UserSchema, many=True)

Specifying Nested Attributes
++++++++++++++++++++++++++++

You can explicitly specify which attributes in the nested fields you want to serialize with the ``only`` argument.

.. code-block:: python

    class BlogSchema2(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema, only=["email"])

    BlogSchema2(blog).data
    # {
    #     'title': u'Something Completely Different',
    #     'author': {'email': u'monty@python.org'}
    # }

.. note::

    If you pass in a string field name to ``only``, only a single value (or flat list of values if ``many=True``) will be returned.

    .. code-block:: python

        class UserSchema(Schema):
            name = fields.String()
            email = fields.Email()
            friends = fields.Nested('self', only='name', many=True)
        # ... create ``user`` ...
        result, errors = UserSchema().dump(user)
        pprint(result)
        # {
        #     "name": "Steve",
        #     "email": "steve@example.com",
        #     "friends": ["Mike", "Joe"]
        # }


You can also exclude fields by passing in an ``exclude`` list.


Two-way Nesting
+++++++++++++++

If you have two objects that nest each other, you can refer to a nested schema by its class name. This allows you to nest Schemas that have not yet been defined.


For example, a representation of an ``Author`` model might include the books that have a foreign-key (many-to-one) relationship to it. Correspondingly, a representation of a ``Book`` will include its author representation.

.. code-block:: python

    class AuthorSchema(Schema):
        # Make sure to use the 'only' or 'exclude' params
        # to avoid infinite recursion
        books = fields.Nested('BookSchema', many=True, exclude=('author', ))
        class Meta:
            fields = ('id', 'name', 'books')

    class BookSchema(Schema):
        author = fields.Nested('AuthorSchema', only=('id', 'name'))
        class Meta:
            fields = ('id', 'title', 'author')

.. code-block:: python

    from marshmallow import pprint
    from mymodels import Author, Book

    author = Author(name='William Faulkner')
    book = Book(title='As I Lay Dying', author=author)
    book_result, errors = BookSchema().dump(book)
    pprint(book_result, indent=2)
    # {
    #   "id": 124,
    #   "title": "As I Lay Dying",
    #   "author": {
    #     "id": 8,
    #     "name": "William Faulkner"
    #   }
    # }

    author_result, errors = AuthorSchema().dump(author)
    pprint(author_result, indent=2)
    # {
    #   "id": 8,
    #   "name": "William Faulkner",
    #   "books": [
    #     {
    #       "id": 124,
    #       "title": "As I Lay Dying"
    #     }
    #   ]
    # }

.. note::
    If you need to, you can also pass the full, module-qualified path to `fields.Nested`. ::

        books = fields.Nested('path.to.BookSchema',
                              many=True, exclude=('author', ))

Nesting A Schema Within Itself
++++++++++++++++++++++++++++++

If the object to be marshalled has a relationship to an object of the same type, you can nest the `Schema` within itself by passing ``"self"`` (with quotes) to the :class:`Nested <marshmallow.fields.Nested>` constructor.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        friends = fields.Nested('self', many=True)
        # Use the 'exclude' argument to avoid infinite recursion
        employer = fields.Nested('self', exclude=('employer', ), default=None)

    user = User("Steve", 'steve@example.com')
    user.friends.append(User("Mike", 'mike@example.com'))
    user.friends.append(User('Joe', 'joe@example.com'))
    user.employer = User('Dirk', 'dirk@example.com')
    result, errors = UserSchema().dump(user)
    pprint(result, indent=2)
    # {
    #     "name": "Steve",
    #     "email": "steve@example.com",
    #     "friends": [
    #         {
    #             "name": "Mike",
    #             "email": "mike@example.com",
    #             "friends": [],
    #             "employer": null
    #         },
    #         {
    #             "name": "Joe",
    #             "email": "joe@example.com",
    #             "friends": [],
    #             "employer": null
    #         }
    #     ],
    #     "employer": {
    #         "name": "Dirk",
    #         "email": "dirk@example.com",
    #         "friends": []
    #     }
    # }



Custom Fields
-------------

There are three ways to create a custom-formatted field for a `Schema`:

- Create a custom :class:`Field <marshmallow.fields.Field>` class
- Use a :class:`Method <marshmallow.fields.Method>` field
- Use a :class:`Function <marshmallow.fields.Function>` field

The method you choose will depend on personal preference and the manner in which you intend to reuse the field.

Creating A Field Class
++++++++++++++++++++++

To create a custom field class, create a subclass of :class:`marshmallow.fields.Field` and implement its :meth:`_format <marshmallow.fields.Field._format>`, :meth:`_serialize <marshmallow.fields.Field._serialize>`, and/or :meth:`_deserialize <marshmallow.fields.Field._deserialize>` methods.

.. code-block:: python

    from marshmallow import fields

    class Titlecased(fields.Field):
        def _format(self, value):
            if value is None:
                return ''
            return value.title()

    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        titlename = TitleCased(attribute="name")

Method Fields
+++++++++++++

A :class:`Method <marshmallow.fields.Method>` field will take the value returned by a method of the Schema. The method must take an ``obj`` parameter which is the object to be serialized.

.. code-block:: python

    class UserSchema(Schema):
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

    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        uppername = fields.Function(lambda obj: obj.name.upper())

Adding Context to Method and Function Fields
++++++++++++++++++++++++++++++++++++++++++++

New in version ``0.5.3``.

You may wish to include other objects when computing a :class:`Function <marshmallow.fields.Function>` or :class:`Method <marshmallow.fields.Method>` field.

As an example, you might want your ``UserSchema`` to output whether or not a ``User`` is the author of a ``Blog``.

In these cases, you can set the ``context`` attribute (a dictionary) of a `Schema`. :class:`Function <marshmallow.fields.Function>` and :class:`Method <marshmallow.fields.Method>` fields will have access to this dictionary.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        is_author = fields.Function(lambda user, ctx: user == ctx['blog'].author)
        likes_bikes = fields.Method('writes_about_bikes')

        def writes_about_bikes(self, user, ctx):
            return 'bicycle' in ctx['blog'].title.lower()

    schema = UserSchema()

    user = User('Freddie Mercury', 'fred@queen.com')
    blog = Blog('Bicycle Blog', author=user)

    schema.context = {'blog': blog}
    data, errors = schema.dump(user)
    data['is_author']  # => True
    data['likes_bikes']  # => True


Next Steps
----------

Check out the :ref:`API Reference <api>` for a full listing of available fields.

Need to add custom post-processing or error handling behavior? See the :ref:`Extending Schemas <extending>` page.

For example applications using marshmallow, check out the :ref:`Examples <examples>` page.
