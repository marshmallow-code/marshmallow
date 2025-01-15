***************************
Validating ``package.json``
***************************

marshmallow can be used to validate configuration according to a schema.
Below is a schema that could be used to validate
``package.json`` files. This example demonstrates the following features:


- Validation and deserialization using `Schema.load <marshmallow.Schema.load>`
- :doc:`Custom fields <../custom_fields>`
- Specifying deserialization keys using ``data_key``
- Including unknown keys using ``unknown = INCLUDE``

.. literalinclude:: ../../examples/package_json_example.py
    :language: python


Given the following ``package.json`` file...

.. literalinclude:: ../../examples/package.json
    :language: json


We can validate it using the above script.

.. code-block:: shell-session

    $ uv run examples/package_json_example.py < examples/package.json
    {'description': 'The Pythonic JavaScript toolkit',
    'dev_dependencies': {'pest': '^23.4.1'},
    'license': 'MIT',
    'main': 'index.js',
    'name': 'dunderscore',
    'scripts': {'test': 'pest'},
    'version': <Version('1.2.3')>}

Notice that our custom field deserialized the version string to a ``Version`` object.

But if we pass an invalid package.json file...

.. literalinclude:: ../../examples/invalid_package.json
    :language: json

We see the corresponding error messages.

.. code-block:: shell-session

    $ uv run examples/package_json_example.py < examples/invalid_package.json
    ERROR: package.json is invalid
    {'homepage': ['Not a valid URL.'], 'version': ['Not a valid version.']}
