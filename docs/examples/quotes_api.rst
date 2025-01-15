*******************************
Quotes API (Flask + SQLAlchemy)
*******************************

Below is a full example of a REST API for a quotes app using `Flask <http://flask.pocoo.org/>`_  and `SQLAlchemy <https://www.sqlalchemy.org/>`_  with marshmallow. It demonstrates a number of features, including:

- Custom validation
- Nesting fields
- Using ``dump_only=True`` to specify read-only fields
- Output filtering using the ``only`` parameter
- Using `@pre_load <marshmallow.decorators.pre_load>` to preprocess input data.

.. literalinclude:: ../../examples/flask_example.py
    :language: python


**Using The API**

Run the app.

.. code-block:: shell-session

    $ uv run examples/flask_example.py

We'll use the `httpie cli <https://httpie.io/cli>`_ to send requests
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
