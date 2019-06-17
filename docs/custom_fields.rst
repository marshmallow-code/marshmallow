
Custom Fields
=============

There are three ways to create a custom-formatted field for a `Schema`:

- Create a custom :class:`Field <marshmallow.fields.Field>` class
- Use a :class:`Method <marshmallow.fields.Method>` field
- Use a :class:`Function <marshmallow.fields.Function>` field

The method you choose will depend on the manner in which you intend to reuse the field.

Creating A Field Class
----------------------

To create a custom field class, create a subclass of :class:`marshmallow.fields.Field` and implement its :meth:`_serialize <marshmallow.fields.Field._serialize>` and/or :meth:`_deserialize <marshmallow.fields.Field._deserialize>` methods.

.. code-block:: python

    from marshmallow import fields


    class TitleCased(fields.Field):
        """Field that serializes to a title case string and deserializes
        to a lower case string.
        """

        def _serialize(self, value, attr, obj, **kwargs):
            if value is None:
                return ""
            return value.title()

        def _deserialize(self, value, attr, data, **kwargs):
            return value.lower()


    class UserSchema(Schema):
        name = fields.String()
        email = fields.String()
        created_at = fields.DateTime()
        titlename = TitleCased(attribute="name")

Method Fields
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

Function Fields
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

.. _adding-context:

Adding Context to `Method` and `Function` Fields
------------------------------------------------

A :class:`Function <marshmallow.fields.Function>` or :class:`Method <marshmallow.fields.Method>` field may need information about its environment to know how to serialize a value.

In these cases, you can set the ``context`` attribute (a dictionary) of a `Schema`. :class:`Function <marshmallow.fields.Function>` and :class:`Method <marshmallow.fields.Method>` fields will have access to this dictionary.

As an example, you might want your ``UserSchema`` to output whether or not a ``User`` is the author of a ``Blog`` or whether the a certain word appears in a ``Blog's`` title.

.. code-block:: python
    :emphasize-lines: 4,8,15

    class UserSchema(Schema):
        name = fields.String()
        # Function fields optionally receive context argument
        is_author = fields.Function(lambda user, context: user == context["blog"].author)
        likes_bikes = fields.Method("writes_about_bikes")

        def writes_about_bikes(self, user):
            return "bicycle" in self.context["blog"].title.lower()


    schema = UserSchema()

    user = User("Freddie Mercury", "fred@queen.com")
    blog = Blog("Bicycle Blog", author=user)

    schema.context = {"blog": blog}
    result = schema.dump(user)
    result["is_author"]  # => True
    result["likes_bikes"]  # => True


Customizing Error Messages
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


Next Steps
----------

- Need to add schema-level validation, post-processing, or error handling behavior? See the :doc:`Extending Schemas <extending>` page.
- For example applications using marshmallow, check out the :doc:`Examples <examples>` page.
