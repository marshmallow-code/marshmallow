Using original input data
-------------------------

If you want to use the original, unprocessed input, you can add ``pass_original=True`` to
`post_load <marshmallow.decorators.post_load>` or `validates_schema <marshmallow.decorators.validates_schema>`.

.. code-block:: python

    from marshmallow import Schema, fields, post_load, ValidationError


    class MySchema(Schema):
        foo = fields.Int()
        bar = fields.Int()

        @post_load(pass_original=True)
        def add_baz_to_bar(self, data, original_data, **kwargs):
            baz = original_data.get("baz")
            if baz:
                data["bar"] = data["bar"] + baz
            return data


    schema = MySchema()
    schema.load({"foo": 1, "bar": 2, "baz": 3})
    # {'foo': 1, 'bar': 5}

.. seealso::

   The default behavior for unspecified fields can be controlled with the ``unknown`` option, see :ref:`Handling Unknown Fields <unknown>` for more information.
