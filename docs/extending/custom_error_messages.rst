Custom error messages
=====================

To customize the schema-level error messages that `load <marshmallow.Schema.load>` and `loads <marshmallow.Schema.loads>` use when raising a `ValidationError <marshmallow.exceptions.ValidationError>`, override the `error_messages <marshmallow.Schema.error_messages>` class variable:

.. code-block:: python

    class MySchema(Schema):
        error_messages = {
            "unknown": "Custom unknown field error message.",
            "type": "Custom invalid type error message.",
        }


Field-level error message defaults can be set on `Field.default_error_messages <marshmallow.fields.Field.default_error_messages>`.


.. code-block:: python

   from marshmallow import Schema, fields

   fields.Field.default_error_messages["required"] = "You missed something!"


   class ArtistSchema(Schema):
       name = fields.Str(required=True)
       label = fields.Str(required=True, error_messages={"required": "Label missing."})


   print(ArtistSchema().validate({}))
   # {'label': ['Label missing.'], 'name': ['You missed something!']}
