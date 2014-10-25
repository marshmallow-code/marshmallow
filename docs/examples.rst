.. _examples:
.. module:: marshmallow

********
Examples
********

The examples below will use `httpie <http://github.com/jkbr/httpie>`_ (a curl-like tool) for testing the APIs.

Text Analysis API (Bottle + TextBlob)
=====================================

Here is a very simple text analysis API using `Bottle <http://bottlepy.org>`_ and `TextBlob <http://textblob.readthedocs.org/>`_ that demonstrates how to declare an object serializer.

Assume that ``TextBlob`` objects have ``polarity``, ``subjectivity``, ``noun_phrase``, ``tags``, and ``words`` properties.

.. literalinclude:: ../examples/textblob_example.py
    :language: python

**Using The API**

First, run the app.

.. code-block:: bash

    $ python textblob_example.py

Then send a POST request with some text.

.. code-block:: bash

    $ http POST localhost:5000/api/v1/analyze text="Simple is better"
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

    - `class Meta` to specify which fields to serialize
    - Output filtering using ``only`` param
    - Using the :func:`error_handler <Serlalizer.error_handler>` decorator


.. literalinclude:: ../examples/flask_example.py
    :language: python


**Using The API**

Run the app.

.. code-block:: bash

    $ python flask_example.py

First we'll POST some quotes.

.. code-block:: bash

    $ http POST localhost:5000/api/v1/quotes/new author="Tim Peters" quote="Beautiful is better than ugly."
    $ http POST localhost:5000/api/v1/quotes/new author="Tim Peters" quote="Now is better than never."
    $ http POST localhost:5000/api/v1/quotes/new author="Peter Hintjens" quote="Simplicity is always better than functionality."

Now we can GET a list of all the quotes.

.. code-block:: bash

    $ http localhost:5000/api/v1/quotes
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

    $ http localhost:5000/api/v1/authors/1
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

This example uses Flask and the `Peewee <http://peewee.readthedocs.org/en/latest/index.html>`_ ORM to create a basic Todo application.

Notice how ``__marshallable__`` is used to define how Peewee model objects get marshalled.

.. literalinclude:: ../examples/peewee_example.py
    :language: python

**Using the API**

After registering a user and creating some todo items in the database, here is an example response.

.. code-block:: bash

    $ http GET localhost:5000/api/v1/todos
    {
        "todos": [
            {
                "content": "Refactor everything",
                "done": false,
                "id": 3,
                "posted_on": ""2014-08-17T14:42:12.479650+00:00",
                "user": {
                    "email": "foo@bar.com",
                    "joined_on": "2014-08-14T13:12:19.179650+00:00"
                }
            },
            {
                "content": "Learn python",
                "done": false,
                "id": 2,
                "posted_on": "2014-08-15T17:41:12.479650+00:00",
                "user": {
                    "email": "foo@bar.com",
                    "joined_on": "2014-08-14T13:12:19.179650+00:00"
                }
            },
            {
                "content": "Install marshmallow",
                "done": false,
                "id": 1,
                "posted_on": "2014-08-15T09:15:12.479650+00:00",
                "user": {
                    "email": "foo@bar.com",
                    "joined_on": "2014-08-14T13:12:19.179650+00:00"
                }
            }
        ]
    }
