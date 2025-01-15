********
Examples
********

The below examples demonstrate how to use marshmallow in various contexts.
To run each example, you will need to have `uv <https://docs.astral.sh/uv/getting-started/installation/>`_ installed.
The examples use `PEP 723 inline metadata <https://peps.python.org/pep-0723/>`_
to declare the dependencies of each script. ``uv`` will install the
dependencies automatically when running these scripts.

Validating ``package.json``
===========================

marshmallow can be used to validate configuration according to a schema.
Below is a schema that could be used to validate
``package.json`` files. This example demonstrates the following features:


- Validation and deserialization using `Schema.load <marshmallow.Schema.load>`
- :doc:`Custom fields <custom_fields>`
- Specifying deserialization keys using ``data_key``
- Including unknown keys using ``unknown = INCLUDE``

.. literalinclude:: ../examples/package_json_example.py
    :language: python


Given the following ``package.json`` file...

.. literalinclude:: ../examples/package.json
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

.. literalinclude:: ../examples/invalid_package.json
    :language: json

We see the corresponding error messages.

.. code-block:: shell-session

    $ uv run examples/package_json_example.py < examples/invalid_package.json
    ERROR: package.json is invalid
    {'homepage': ['Not a valid URL.'], 'version': ['Not a valid version.']}

Quotes API (Flask + SQLAlchemy)
===============================

Below is a full example of a REST API for a quotes app using `Flask <http://flask.pocoo.org/>`_  and `SQLAlchemy <https://www.sqlalchemy.org/>`_  with marshmallow. It demonstrates a number of features, including:

- Custom validation
- Nesting fields
- Using ``dump_only=True`` to specify read-only fields
- Output filtering using the ``only`` parameter
- Using `@pre_load <marshmallow.decorators.pre_load>` to preprocess input data.

.. literalinclude:: ../examples/flask_example.py
    :language: python


**Using The API**

Run the app.

.. code-block:: shell-session

    $ uv run examples/flask_example.py

We'll use the [httpie cli](https://httpie.io/cli) to send requests
Install it with ``uv``.

.. code-block:: shell-session

    $ uv tool install httpie

First we'll POST some quotes.

.. code-block:: shell-session

    $ http POST :5000/quotes/ author="Tim Peters" content="Beautiful is better than ugly."
    $ http POST :5000/quotes/ author="Tim Peters" content="Now is better than never."
    $ http POST :5000/quotes/ author="Peter Hintjens" content="Simplicity is always better than functionality."


If we provide invalid input data, we get 400 error response. Let's omit "author" from the input data.

.. code-block:: shell-session

    $ http POST :5000/quotes/ content="I have no author"
    {
        "author": [
            "Data not provided."
        ]
    }

Now we can GET a list of all the quotes.

.. code-block:: shell-session

    $ http :5000/quotes/
    {
        "quotes": [
            {
                "content": "Beautiful is better than ugly.",
                "id": 1
            },
            {
                "content": "Now is better than never.",
                "id": 2
            },
            {
                "content": "Simplicity is always better than functionality.",
                "id": 3
            }
        ]
    }

We can also GET the quotes for a single author.

.. code-block:: shell-session

    $ http :5000/authors/1
    {
        "author": {
            "first": "Tim",
            "formatted_name": "Peters, Tim",
            "id": 1,
            "last": "Peters"
        },
        "quotes": [
            {
                "content": "Beautiful is better than ugly.",
                "id": 1
            },
            {
                "content": "Now is better than never.",
                "id": 2
            }
        ]
    }


Inflection (camel-cased keys)
=============================

HTTP APIs will often use camel-cased keys for their input and output representations. This example shows how you can use the
`Schema.on_bind_field <marshmallow.Schema.on_bind_field>` hook to automatically inflect keys.

.. literalinclude:: ../examples/inflection_example.py
    :language: python
