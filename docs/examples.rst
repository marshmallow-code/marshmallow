.. module:: marshmallow

********
Examples
********

The examples below will use `httpie <http://github.com/jkbr/httpie>`_ (a curl-like tool) for testing the APIs.

Text Analysis API (Bottle + TextBlob)
=====================================

Here is a very simple text analysis API using `Bottle <http://bottlepy.org>`_ and `TextBlob <http://textblob.readthedocs.io/>`_ that demonstrates how to declare an object serializer.

Assume that ``TextBlob`` objects have ``polarity``, ``subjectivity``, ``noun_phrase``, ``tags``, and ``words`` properties.

.. literalinclude:: ../examples/textblob_example.py
    :language: python

**Using The API**

First, run the app.

.. code-block:: bash

    $ python textblob_example.py

Then send a POST request with some text.

.. code-block:: bash

    $ http POST :5000/api/v1/analyze text="Simple is better"
    HTTP/1.0 200 OK
    Content-Length: 189
    Content-Type: application/json
    Date: Wed, 13 Nov 2013 08:58:40 GMT
    Server: WSGIServer/0.1 Python/2.7.5

    {
        "chunks": [
            "simple"
        ],
        "discrete_sentiment": "positive",
        "polarity": 0.25,
        "subjectivity": 0.4285714285714286,
        "tags": [
            [
                "Simple",
                "NN"
            ],
            [
                "is",
                "VBZ"
            ],
            [
                "better",
                "JJR"
            ]
        ],
        "word_count": 3
    }


Quotes API (Flask + SQLAlchemy)
================================

Below is a full example of a REST API for a quotes app using `Flask <http://flask.pocoo.org/>`_  and `SQLAlchemy <http://www.sqlalchemy.org/>`_  with marshmallow. It demonstrates a number of features, including:

    - Validation and deserialization using :meth:`Schema.load`.
    - Custom validation
    - Nesting fields
    - Using ``dump_only=True`` to specify read-only fields
    - Output filtering using the ``only`` parameter
    - Using `@pre_load <marshmallow.decorators.pre_load>` to preprocess input data.

.. literalinclude:: ../examples/flask_example.py
    :language: python


**Using The API**

Run the app.

.. code-block:: bash

    $ python flask_example.py

First we'll POST some quotes.

.. code-block:: bash

    $ http POST :5000/quotes/ author="Tim Peters" content="Beautiful is better than ugly."
    $ http POST :5000/quotes/ author="Tim Peters" content="Now is better than never."
    $ http POST :5000/quotes/ author="Peter Hintjens" content="Simplicity is always better than functionality."


If we provide invalid input data, we get 400 error response. Let's omit "author" from the input data.

.. code-block:: bash

    $ http POST :5000/quotes/ content="I have no author"
    {
        "author": [
            "Data not provided."
        ]
    }

Now we can GET a list of all the quotes.

.. code-block:: bash

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

.. code-block:: bash

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

ToDo API (Flask + Peewee)
=========================

This example uses Flask and the `Peewee <http://peewee.readthedocs.io/en/latest/index.html>`_ ORM to create a basic Todo application.

Here, we use `Schema.load <marshmallow.Schema.load>` to validate and deserialize input data to model data. Also notice how `pre_load <marshmallow.decorators.pre_load>` is used to clean input data and `post_load <marshmallow.decorators.post_load>` is used to add an envelope to response data.

.. literalinclude:: ../examples/peewee_example.py
    :language: python

**Using the API**

After registering a user and creating some todo items in the database, here is an example response.

.. code-block:: bash

    $ http GET :5000/todos/
    {
        "todos": [
            {
                "content": "Install marshmallow",
                "done": false,
                "id": 1,
                "posted_on": "2015-05-05T01:51:12.832232+00:00",
                "user": {
                    "user": {
                        "email": "foo@bar.com",
                        "id": 1
                    }
                }
            },
            {
                "content": "Learn Python",
                "done": false,
                "id": 2,
                "posted_on": "2015-05-05T01:51:20.728052+00:00",
                "user": {
                    "user": {
                        "email": "foo@bar.com",
                        "id": 1
                    }
                }
            },
            {
                "content": "Refactor everything",
                "done": false,
                "id": 3,
                "posted_on": "2015-05-05T01:51:25.970153+00:00",
                "user": {
                    "user": {
                        "email": "foo@bar.com",
                        "id": 1
                    }
                }
            }
        ]
    }
