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
