Custom fields
=============

There are three ways to create a custom-formatted field for a `Schema <marshmallow.Schema>`:

- Create a custom :class:`Field <marshmallow.fields.Field>` class
- Use a :class:`Method <marshmallow.fields.Method>` field
- Use a :class:`Function <marshmallow.fields.Function>` field

The method you choose will depend on the manner in which you intend to reuse the field.

Creating a field class
----------------------

To create a custom field class, create a subclass of :class:`marshmallow.fields.Field` and implement its :meth:`_serialize <marshmallow.fields.Field._serialize>` and/or :meth:`_deserialize <marshmallow.fields.Field._deserialize>` methods.
Field's type argument is the internal type, i.e. the type that the field deserializes to.

.. code-block:: python

    from marshmallow import fields, ValidationError


    class PinCode(fields.Field[list[int]]):
        """Field that serializes to a string of numbers and deserializes
        to a list of numbers.
        """

        def _serialize(self, value, attr, obj, **kwargs):
            if value is None:
                return ""
            return "".join(str(d) for d in value)

        def _deserialize(self, value, attr, data, **kwargs):
            try:
                return [int(c) for c in value]
            except ValueError as error:
                raise ValidationError("Pin codes must contain only digits.") from error


    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        pin_code = PinCode()

Method fields
-------------

A :class:`Method <marshmallow.fields.Method>` field will serialize to the value returned by a method of the Schema. The method must take an ``obj`` parameter which is the object to be serialized.

.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        since_created = fields.Method("get_days_since_created")

        def get_days_since_created(self, obj):
            return dt.datetime.now().day - obj.created_at.day

Function fields
---------------

A :class:`Function <marshmallow.fields.Function>` field will serialize the value of a function that is passed directly to it. Like a :class:`Method <marshmallow.fields.Method>` field, the function must take a single argument ``obj``.


.. code-block:: python

    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        uppername = fields.Function(lambda obj: obj.name.upper())

`Method` and `Function` field deserialization
---------------------------------------------

Both :class:`Function <marshmallow.fields.Function>` and :class:`Method <marshmallow.fields.Method>` receive an optional ``deserialize`` argument which defines how the field should be deserialized. The method or function passed to ``deserialize`` receives the input value for the field.

.. code-block:: python

    class UserSchema(Schema):
        # `Method` takes a method name (str), Function takes a callable
        balance = fields.Method("get_balance", deserialize="load_balance")

        def get_balance(self, obj):
            return obj.income - obj.debt

        def load_balance(self, value):
            return float(value)


    schema = UserSchema()
    result = schema.load({"balance": "100.00"})
    result["balance"]  # => 100.0

.. _using_context:

Using context
-------------

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


Customizing error messages
--------------------------

Validation error messages for fields can be configured at the class or instance level.

At the class level, default error messages are defined as a mapping from error codes to error messages.

.. code-block:: python

    from marshmallow import fields


    class MyDate(fields.Date):
        default_error_messages = {"invalid": "Please provide a valid date."}

.. note::
    A `Field's` ``default_error_messages`` dictionary gets merged with its parent classes' ``default_error_messages`` dictionaries.

Error messages can also be passed to a `Field's` constructor.

.. code-block:: python

    from marshmallow import Schema, fields


    class UserSchema(Schema):
        name = fields.Str(
            required=True, error_messages={"required": "Please provide a name."}
        )


Next steps
----------

- Need to add schema-level validation, post-processing, or error handling behavior? See the :doc:`extending/index` page.
- For example applications using marshmallow, check out the :doc:`examples/index` page.
