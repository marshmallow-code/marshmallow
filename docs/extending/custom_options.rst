Custom `class Meta <marshmallow.Schema.Meta>` options
=====================================================

`class Meta <marshmallow.Schema.Meta>` options are a way to configure and modify a `Schema's <Schema>` behavior. See `marshmallow.Schema.Meta` for a listing of available options.

You can add custom `class Meta <marshmallow.Schema.Meta>` options by subclassing `marshmallow.SchemaOpts`.

Example: Enveloping, revisited
------------------------------

Let's build upon the :ref:`previous enveloping implementation <enveloping_1>` above for adding an envelope to serialized output. 
This time, we will allow the envelope key to be customizable with `class Meta <marshmallow.Schema.Meta>` options.

::

    # Example outputs
    {
        'user': {
            'name': 'Keith',
            'email': 'keith@stones.com'
        }
    }
    # List output
    {
        'users': [{'name': 'Keith'}, {'name': 'Mick'}]
    }


First, we'll add our namespace configuration to a custom options class.

.. code-block:: python

    from marshmallow import Schema, SchemaOpts


    class NamespaceOpts(SchemaOpts):
        """Same as the default class Meta options, but adds "name" and
        "plural_name" options for enveloping.
        """

        def __init__(self, meta, **kwargs):
            SchemaOpts.__init__(self, meta, **kwargs)
            self.name = getattr(meta, "name", None)
            self.plural_name = getattr(meta, "plural_name", self.name)


Then we create a custom :class:`Schema` that uses our options class.

.. code-block:: python

    class NamespacedSchema(Schema):
        OPTIONS_CLASS = NamespaceOpts

        @pre_load(pass_many=True)
        def unwrap_envelope(self, data, many, **kwargs):
            key = self.opts.plural_name if many else self.opts.name
            return data[key]

        @post_dump(pass_many=True)
        def wrap_with_envelope(self, data, many, **kwargs):
            key = self.opts.plural_name if many else self.opts.name
            return {key: data}


Our application schemas can now inherit from our custom schema class.

.. code-block:: python

    class UserSchema(NamespacedSchema):
        name = fields.String()
        email = fields.Email()

        class Meta:
            name = "user"
            plural_name = "users"


    ser = UserSchema()
    user = User("Keith", email="keith@stones.com")
    result = ser.dump(user)
    result  # {"user": {"name": "Keith", "email": "keith@stones.com"}}
