Nesting schemas
===============

Schemas can be nested to represent relationships between objects (e.g. foreign key relationships). 
For example, a ``Blog`` may have an author represented by a ``User``.
And a ``User`` may have many friends, each of which is a ``User``.

.. code-block:: python

    from __future__ import annotations  # Enable newer type annotation syntax

    import datetime as dt
    from dataclasses import dataclass, field


    @dataclass
    class User:
        name: str
        email: str
        created_at: dt.datetime = field(default_factory=dt.datetime.now)
        friends: list[User] = field(default_factory=list)
        employer: User | None = None


    @dataclass
    class Blog:
        title: str
        author: User

Use a :class:`Nested <marshmallow.fields.Nested>` field to represent the relationship, passing in a nested schema.

.. code-block:: python

    from marshmallow import Schema, fields


    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()


    class BlogSchema(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema)

The serialized blog will have the nested user representation.

.. code-block:: python

    from pprint import pprint

    user = User(name="Monty", email="monty@python.org")
    blog = Blog(title="Something Completely Different", author=user)
    result = BlogSchema().dump(blog)
    pprint(result)
    # {'title': u'Something Completely Different',
    #  'author': {'name': u'Monty',
    #             'email': u'monty@python.org',
    #             'created_at': '2014-08-17T14:58:57.600623+00:00'}}

.. note::
    If the field is a collection of nested objects, pass the `Nested <marshmallow.fields.Nested>` field to `List <marshmallow.fields.List>`.

    .. code-block:: python

        collaborators = fields.List(fields.Nested(UserSchema))

.. _specifying-nested-fields:

Specifying which fields to nest
-------------------------------

You can explicitly specify which attributes of the nested objects you want to (de)serialize with the ``only`` argument to the schema.

.. code-block:: python

    class BlogSchema2(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema(only=("email",)))


    schema = BlogSchema2()
    result = schema.dump(blog)
    pprint(result)
    # {
    #     'title': u'Something Completely Different',
    #     'author': {'email': u'monty@python.org'}
    # }

Dotted paths may be passed to ``only`` and ``exclude`` to specify nested attributes.

.. code-block:: python

    class SiteSchema(Schema):
        blog = fields.Nested(BlogSchema2)


    schema = SiteSchema(only=("blog.author.email",))
    result = schema.dump(site)
    pprint(result)
    # {
    #     'blog': {
    #         'author': {'email': u'monty@python.org'}
    #     }
    # }

You can replace nested data with a single value (or flat list of values if ``many=True``) using the :class:`Pluck <marshmallow.fields.Pluck>` field.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        friends = fields.Pluck("self", "name", many=True)


    # ... create ``user`` ...
    serialized_data = UserSchema().dump(user)
    pprint(serialized_data)
    # {
    #     "name": "Steve",
    #     "email": "steve@example.com",
    #     "friends": ["Mike", "Joe"]
    # }
    deserialized_data = UserSchema().load(result)
    pprint(deserialized_data)
    # {
    #     "name": "Steve",
    #     "email": "steve@example.com",
    #     "friends": [{"name": "Mike"}, {"name": "Joe"}]
    # }


.. _partial-loading:

Partial loading
---------------

Nested schemas also inherit the ``partial`` parameter of the parent ``load`` call.

.. code-block:: python

    class UserSchemaStrict(Schema):
        name = fields.String(required=True)
        email = fields.Email()
        created_at = fields.DateTime(required=True)


    class BlogSchemaStrict(Schema):
        title = fields.String(required=True)
        author = fields.Nested(UserSchemaStrict, required=True)


    schema = BlogSchemaStrict()
    blog = {"title": "Something Completely Different", "author": {}}
    result = schema.load(blog, partial=True)
    pprint(result)
    # {'author': {}, 'title': 'Something Completely Different'}

You can specify a subset of the fields to allow partial loading using dot delimiters.

.. code-block:: python

    author = {"name": "Monty"}
    blog = {"title": "Something Completely Different", "author": author}
    result = schema.load(blog, partial=("title", "author.created_at"))
    pprint(result)
    # {'author': {'name': 'Monty'}, 'title': 'Something Completely Different'}

.. _two-way-nesting:

Two-way nesting
---------------

If you have two objects that nest each other, you can pass a callable to `Nested <marshmallow.fields.Nested>`.
This allows you to resolve order-of-declaration issues, such as when one schema nests a schema that is declared below it.

For example, a representation of an ``Author`` model might include the books that have a many-to-one relationship to it.
Correspondingly, a representation of a ``Book`` will include its author representation.

.. code-block:: python

    class BookSchema(Schema):
        id = fields.Int(dump_only=True)
        title = fields.Str()

        # Make sure to use the 'only' or 'exclude'
        # to avoid infinite recursion
        author = fields.Nested(lambda: AuthorSchema(only=("id", "title")))


    class AuthorSchema(Schema):
        id = fields.Int(dump_only=True)
        title = fields.Str()

        books = fields.List(fields.Nested(BookSchema(exclude=("author",))))


.. code-block:: python

    from pprint import pprint
    from mymodels import Author, Book

    author = Author(name="William Faulkner")
    book = Book(title="As I Lay Dying", author=author)
    book_result = BookSchema().dump(book)
    pprint(book_result, indent=2)
    # {
    #   "id": 124,
    #   "title": "As I Lay Dying",
    #   "author": {
    #     "id": 8,
    #     "name": "William Faulkner"
    #   }
    # }

    author_result = AuthorSchema().dump(author)
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

You can also pass a class name as a string to `Nested <marshmallow.fields.Nested>`.
This is useful for avoiding circular imports when your schemas are located in different modules.

.. code-block:: python

    # books.py
    from marshmallow import Schema, fields


    class BookSchema(Schema):
        id = fields.Int(dump_only=True)
        title = fields.Str()

        author = fields.Nested("AuthorSchema", only=("id", "title"))

.. code-block:: python

    # authors.py
    from marshmallow import Schema, fields


    class AuthorSchema(Schema):
        id = fields.Int(dump_only=True)
        title = fields.Str()

        books = fields.List(fields.Nested("BookSchema", exclude=("author",)))

.. note::

    If you have multiple schemas with the same class name, you must pass the full, module-qualified path. ::

        author = fields.Nested("authors.BookSchema", only=("id", "title"))

.. _self-nesting:

Nesting a schema within itself
------------------------------

If the object to be marshalled has a relationship to an object of the same type, you can nest the `Schema <marshmallow.Schema>` within itself by passing a callable that returns an instance of the same schema.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        # Use the 'exclude' argument to avoid infinite recursion
        employer = fields.Nested(lambda: UserSchema(exclude=("employer",)))
        friends = fields.List(fields.Nested(lambda: UserSchema()))


    user = User("Steve", "steve@example.com")
    user.friends.append(User("Mike", "mike@example.com"))
    user.friends.append(User("Joe", "joe@example.com"))
    user.employer = User("Dirk", "dirk@example.com")
    result = UserSchema().dump(user)
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

Next steps
----------

- Want to create your own field type? See the :doc:`custom_fields` page.
- Need to add schema-level validation, post-processing, or error handling behavior? See the :doc:`extending/index` page.
- For more detailed usage examples, check out the :doc:`examples/index` page.
