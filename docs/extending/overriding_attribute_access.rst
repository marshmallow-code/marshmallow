Overriding how attributes are accessed
======================================

By default, marshmallow uses `utils.get_value <marshmallow.utils.get_value>` to pull attributes from various types of objects for serialization. This will work for *most* use cases.

However, if you want to specify how values are accessed from an object, you can override the :meth:`get_attribute <marshmallow.Schema.get_attribute>` method.

.. code-block:: python

    class UserDictSchema(Schema):
        name = fields.Str()
        email = fields.Email()

        # If we know we're only serializing dictionaries, we can
        # use dict.get for all input objects
        def get_attribute(self, obj, key, default):
            return obj.get(key, default)
