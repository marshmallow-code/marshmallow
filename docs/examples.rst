.. _examples:

********
Examples
********

The examples below will use `httpie <http://github.com/jkbr/httpie>`_ (a curl-like tool) for testing the APIs.

Text Analysis API (Bottle + TextBlob)
=====================================

Here is a very simple text analysis API using `Bottle <http://bottlepy.org>`_ and `TextBlob <http://textblob.readthedocs.org/>`_ that demonstrates how to declare an object serializer.

Assume that ``TextBlob`` objects have ``polarity``, ``subjectivity``, ``noun_phrase``, ``tags``, and ``words`` properties.

.. code-block:: python

    from bottle import route, request, run
    from textblob import TextBlob, Word
    from marshmallow import Serializer, fields


    class BlobSerializer(Serializer):
        polarity = fields.Float()
        subjectivity = fields.Float()
        chunks = fields.List(fields.String, attribute="noun_phrases")
        tags = fields.Raw()
        discrete_sentiment = fields.Method("get_discrete_sentiment")
        word_count = fields.Function(lambda obj: len(obj.words))

        def get_discrete_sentiment(self, obj):
            if obj.polarity > 0.1:
                return 'positive'
            elif obj.polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'


    @route("/api/v1/analyze", method="POST")
    def analyze():
        blob = TextBlob(request.json['text'])
        return BlobSerializer(blob).data


    run(port=5000)

Using The API
-------------

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


Quotes API (Flask + SQL-Alchemy)
================================

Below is a full example of a REST API for a quotes app using `Flask <http://flask.pocoo.org/>`_  and `SQLAlchemy <http://www.sqlalchemy.org/>`_  with marshmallow. It demonstrates the use of *class Meta* to specify which
fields to serialize.

.. code-block:: python

    from datetime import datetime

    from flask import Flask, jsonify, request, Response
    from flask.ext.sqlalchemy import SQLAlchemy
    from sqlalchemy.exc import IntegrityError
    from marshmallow import Serializer, fields

    app = Flask(__name__)
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:////tmp/test.db'
    db = SQLAlchemy(app)

    ##### MODELS #####

    class Author(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        first_name = db.Column(db.String(80))
        last_name = db.Column(db.String(80))

        def __init__(self, first_name, last_name):
            self.first_name = first_name
            self.last_name = last_name

        def __repr__(self):
            return '<Author "{0} {1}">'.format(self.first_name, self.last_name)

    class Quote(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.String, nullable=False)
        author_id = db.Column(db.Integer, db.ForeignKey("author.id"))
        author = db.relationship("Author",
                            backref=db.backref("quotes", lazy="dynamic"))
        posted_at = db.Column(db.DateTime)

        def __init__(self, content, author):
            self.author = author
            self.content = content
            self.posted_at = datetime.utcnow()

        def __repr__(self):
            return '<Quote "{0}">'.format(self.content)

    ##### SERIALIZERS #####

    class AuthorSerializer(Serializer):
        formatted = fields.Method("get_formatted_name")

        def get_formatted_name(self, obj):
            return "{last}, {first}".format(last=obj.last_name, first=obj.first_name)

        class Meta:
            fields = ("id", "first_name", "last_name", 'formatted')

    class QuoteSerializer(Serializer):
        author = fields.Nested(AuthorSerializer)

        class Meta:
            fields = ("content", "posted_at", 'author')

    ##### API #####

    @app.route("/quotes", methods=["GET", "POST"])
    def quotes():
        # On POST requests, add a new quote to the database
        if request.method == "POST":
            first, last = request.json['author'].split(" ")
            quote = request.json['quote']
            author = Author.query.filter_by(first_name=first, last_name=last).first()
            if author is None:
                # Create a new author
                author = Author(first, last)
                db.session.add(author)
            # Create new quote
            quote = Quote(quote, author)
            db.session.add(quote)
            db.session.commit()
            return jsonify({"success": True})
        else:  # For GET requests, just return all the quotes
            quotes = Quote.query.all()
            serialized = QuoteSerializer(quotes)
            return Response(serialized.json, mimetype="application/json")

    @app.route("/authors", methods=["GET", "POST"])
    def authors():
        # On POST requests, create a new author
        if request.method == "POST":
            serialized = AuthorSerializer(request.json)
            if serialized.is_valid():
                author = Author(request.json['first_name'], request.json['last_name'])
                success = True
                try:
                    db.session.add(author)
                    db.session.commit()
                except IntegrityError:
                    success = False
            else:
                success = False
            return jsonify({"success": success})
        else:  # For GET requests, just return all the users
            authors = Author.query.all()
            return Response(AuthorSerializer(authors).json, mimetype="application/json")


    if __name__ == '__main__':
        db.create_all()
        app.run(port=5000)




Using the API
-------------

Run the app.

.. code-block:: bash

    $ python flask_example.py

Send a POST request to ``/authors`` to create a new author.

.. code-block:: bash

    $ http POST localhost:5000/authors first_name="Tim" last_name="Peters"
    HTTP/1.0 200 OK
    Content-Length: 21
    Content-Type: application/json
    Date: Wed, 13 Nov 2013 08:40:51 GMT
    Server: Werkzeug/0.9.4 Python/2.7.5

    {
        "success": true
    }

Next we'll create a new quote by sending a POST request to ``/quotes``.

.. code-block:: bash

    $ http POST localhost:5000/quotes author="Tim Peters" quote="Simple is better than complex."

We can get the serialized quotes by sending a GET request to ``/quotes``.

.. code-block:: bash

    $ http GET localhost:5000/quotes
    HTTP/1.0 200 OK
    Content-Length: 188
    Content-Type: application/json
    Date: Wed, 13 Nov 2013 09:04:33 GMT
    Server: Werkzeug/0.9.4 Python/2.7.5

    [
        {
            "author": {
                "first_name": "Tim",
                "formatted": "Peters, Tim",
                "id": 1,
                "last_name": "Peters"
            },
            "content": "Simple is better than complex.",
            "posted_at": "Wed, 13 Nov 2013 08:41:58 -0000"
        }
    ]

