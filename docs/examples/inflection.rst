*****************************
Inflection (camel-cased keys)
*****************************

HTTP APIs will often use camel-cased keys for their input and output representations. This example shows how you can use the
`Schema.on_bind_field <marshmallow.Schema.on_bind_field>` hook to automatically inflect keys.

.. literalinclude:: ../../examples/inflection_example.py
    :language: python

To run the example:

.. code-block:: shell-session

    $ uv run examples/inflection_example.py
    Loaded data:
    {'first_name': 'David', 'last_name': 'Bowie'}
    Dumped data:
    {'firstName': 'David', 'lastName': 'Bowie'}
