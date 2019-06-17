Nesting Schemas
===============

Schemas can be nested to represent relationships between objects (e.g. foreign key relationships). For example, a ``Blog`` may have an author represented by a User object.

.. code-block:: python
    :emphasize-lines: 14

    import datetime as dt


    class User:
        def __init__(self, name, email):
            self.name = name
            self.email = email
            self.created_at = dt.datetime.now()
            self.friends = []
            self.employer = None


    class Blog:
        def __init__(self, title, author):
            self.title = title
            self.author = author  # A User object

Use a :class:`Nested <marshmallow.fields.Nested>` field to represent the relationship, passing in a nested schema class.

.. code-block:: python
    :emphasize-lines: 10

    from marshmallow import Schema, fields, pprint


    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        created_at = fields.DateTime()


    class BlogSchema(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema)

The serialized blog will have the nested user representation.

.. code-block:: python

    user = User(name="Monty", email="monty@python.org")
    blog = Blog(title="Something Completely Different", author=user)
    result = BlogSchema().dump(blog)
    pprint(result)
    # {'title': u'Something Completely Different',
    #  'author': {'name': u'Monty',
    #             'email': u'monty@python.org',
    #             'created_at': '2014-08-17T14:58:57.600623+00:00'}}

.. note::
    If the field is a collection of nested objects, you must set ``many=True``.

    .. code-block:: python

        collaborators = fields.Nested(UserSchema, many=True)

.. _specifying-nested-fields:

Specifying Which Fields to Nest
-------------------------------

You can explicitly specify which attributes of the nested objects you want to serialize with the ``only`` argument.

.. code-block:: python
    :emphasize-lines: 3

    class BlogSchema2(Schema):
        title = fields.String()
        author = fields.Nested(UserSchema, only=["email"])


    schema = BlogSchema2()
    result = schema.dump(blog)
    pprint(result)
    # {
    #     'title': u'Something Completely Different',
    #     'author': {'email': u'monty@python.org'}
    # }

You can represent the attributes of deeply nested objects using dot delimiters.

.. code-block:: python
    :emphasize-lines: 5

    class SiteSchema(Schema):
        blog = fields.Nested(BlogSchema2)


    schema = SiteSchema(only=["blog.author.email"])
    result = schema.dump(site)
    pprint(result)
    # {
    #     'blog': {
    #         'author': {'email': u'monty@python.org'}
    #     }
    # }

You can replace nested data with a single value (or flat list of values if ``many=True``) using the :class:`Pluck <marshmallow.fields.Pluck>` field.

.. code-block:: python
    :emphasize-lines: 4, 11, 18

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


You can also exclude fields by passing in an ``exclude`` list. This argument also allows representing the attributes of deeply nested objects using dot delimiters.

.. _partial-loading:

Partial Loading
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

Two-way Nesting
---------------

If you have two objects that nest each other, you can refer to a nested schema by its class name. This allows you to nest Schemas that have not yet been defined.


For example, a representation of an ``Author`` model might include the books that have a foreign-key (many-to-one) relationship to it. Correspondingly, a representation of a ``Book`` will include its author representation.

.. code-block:: python
    :emphasize-lines: 4

    class AuthorSchema(Schema):
        # Make sure to use the 'only' or 'exclude' params
        # to avoid infinite recursion
        books = fields.Nested("BookSchema", many=True, exclude=("author",))

        class Meta:
            fields = ("id", "name", "books")


    class BookSchema(Schema):
        author = fields.Nested(AuthorSchema, only=("id", "name"))

        class Meta:
            fields = ("id", "title", "author")

.. code-block:: python

    from marshmallow import pprint
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

.. note::
    If you need to, you can also pass the full, module-qualified path to `fields.Nested`. ::

        books = fields.Nested('path.to.BookSchema',
                              many=True, exclude=('author', ))

.. _self-nesting:

Nesting A Schema Within Itself
------------------------------

If the object to be marshalled has a relationship to an object of the same type, you can nest the `Schema` within itself by passing ``"self"`` (with quotes) to the :class:`Nested <marshmallow.fields.Nested>` constructor.

.. code-block:: python
    :emphasize-lines: 4,6

    class UserSchema(Schema):
        name = fields.String()
        email = fields.Email()
        friends = fields.Nested("self", many=True)
        # Use the 'exclude' argument to avoid infinite recursion
        employer = fields.Nested("self", exclude=("employer",), default=None)


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

Next Steps
----------

- Want to create your own field type? See the :doc:`Custom Fields <custom_fields>` page.
- Need to add schema-level validation, post-processing, or error handling behavior? See the :doc:`Extending Schemas <extending>` page.
- For example applications using marshmallow, check out the :doc:`Examples <examples>` page.
