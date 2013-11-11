********
Examples
********


With Flask
==========

Below is a full example of a REST API for a quotes app using Flask and SQL-Alchemy with marshmallow.

.. code-block:: python

    from datetime import datetime

    from flask import Flask, jsonify, request
    from sqlalchemy.exc import IntegrityError
    from flask.ext.sqlalchemy import SQLAlchemy
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

    ##### Serializers #####

    class AuthorSerializer(Serializer):
        id = fields.Integer()
        first_name = fields.String()
        last_name = fields.String()
        formatted = fields.Method("get_formatted_name")

        def get_formatted_name(self, obj):
            return "{last}, {first}".format(last=obj.last_name, first=obj.first_name)

    class QuoteSerializer(Serializer):
        content = fields.String()
        author = fields.Nested(AuthorSerializer)
        posted_at = fields.DateTime()

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
            return serialized.json

    @app.route("/authors", methods=["GET", "POST"])
    def authors():
        # On POST requests, create a new author
        if request.method == "POST":
            serialized = AuthorSerializer(request.json)
            if serialized.is_valid():  # Validate the POSTed data
                author = Author(request.json['first_name'], request.json['last_name'])
                success = True
                errors = {}
                try:
                    db.session.add(author)
                    db.session.commit()
                except IntegrityError:
                    errors['author'] = "Author already exists."
                    success = False
            else:
                errors.update(serialized.errors)
                success = False
            return jsonify({"success": success, "errors": errors})
        else:  # For GET requests, just return all the users
            authors = Author.query.all()
            return AuthorSerializer(authors).json


    if __name__ == '__main__':
        db.create_all()
        app.run(port=5000)


Using the API
-------------

We'll use `requests <http://python-requests.org>`_ to test our API.

First, we'll send a POST request to ``/authors`` to create a new author.

.. code-block:: python

    >>> import requests
    >>> import json
    >>> headers = {"Content-Type": "application/json"}
    >>> base = "http://localhost:5000"
    >>> r = requests.post(base + "/authors", json.dumps({"first_name": "Tim", "last_name": "Peters"}), headers=headers)
    >>> r = requests.get(base + "/authors")
    >>> r.json()
    [{u'first_name': u'Tim', u'last_name': u'Peters', u'formatted': u'Peters, Tim', u'id': 1}]

Next we'll create a new quote by sending a POST request to ``/quotes``.

.. code-block:: python

    >>> payload = json.dumps({"author": "Tim Peters", "quote": "Simple is better than complex"})
    >>> r = requests.post(base + "/quotes", payload, headers=headers)

We can get the serialized quotes by sending a GET request to ``/quotes``.

    >>> r = requests.get(base + "/quotes")
    >>> r.json()
    [{u'content': u'Simple is better than complex', u'posted_at': u'Mon, 11 Nov 2013 21:37:19 -0000', u'author': {u'first_name': u'Tim', u'last_name': u'Peters', u'formatted': u'Peters, Tim', u'id': 1}}]
