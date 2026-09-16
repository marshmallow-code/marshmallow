Using context
=============

.. _using_context:

A field may need information about its environment to know how to (de)serialize a value.

You can use the experimental `Context <marshmallow.experimental.context.Context>` class
to set and retrieve context.

Let's say your ``UserSchema`` needs to output
whether or not a ``User`` is the author of a ``Blog`` or
whether a certain word appears in a ``Blog's`` title.

.. code-block:: python

    import typing
    from dataclasses import dataclass

    from marshmallow import Schema, fields
    from marshmallow.experimental.context import Context


    @dataclass
    class User:
        name: str


    @dataclass
    class Blog:
        title: str
        author: User


    class ContextDict(typing.TypedDict):
        blog: Blog


    class UserSchema(Schema):
        name = fields.String()

        is_author = fields.Function(
            lambda user: user == Context[ContextDict].get()["blog"].author
        )
        likes_bikes = fields.Method("writes_about_bikes")

        def writes_about_bikes(self, user: User) -> bool:
            return "bicycle" in Context[ContextDict].get()["blog"].title.lower()

.. note::
    You can use `Context.get <marshmallow.experimental.context.Context.get>`
    within custom fields, pre-/post-processing methods, and validators.

When (de)serializing, set the context by using `Context <marshmallow.experimental.context.Context>` as a context manager.

.. code-block:: python


    user = User("Freddie Mercury", "fred@queen.com")
    blog = Blog("Bicycle Blog", author=user)

    schema = UserSchema()
    with Context({"blog": blog}):
        result = schema.dump(user)
        print(result["is_author"])  # => True
        print(result["likes_bikes"])  # => True
