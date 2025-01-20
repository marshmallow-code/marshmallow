Custom error handling
=====================

By default, `Schema.load <marshmallow.Schema.load>` will raise a :exc:`ValidationError <marshmallow.exceptions.ValidationError>` if passed invalid data.

You can specify a custom error-handling function for a :class:`Schema` by overriding the `handle_error <marshmallow.Schema.handle_error>`  method. The method receives the :exc:`ValidationError <marshmallow.exceptions.ValidationError>` and the original input data to be deserialized.

.. code-block:: python

    import logging
    from marshmallow import Schema, fields


    class AppError(Exception):
        pass


    class UserSchema(Schema):
        email = fields.Email()

        def handle_error(self, exc, data, **kwargs):
            """Log and raise our custom exception when (de)serialization fails."""
            logging.error(exc.messages)
            raise AppError("An error occurred with input: {0}".format(data))


    schema = UserSchema()
    schema.load({"email": "invalid-email"})  # raises AppError
