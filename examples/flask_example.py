from datetime import datetime

from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from marshmallow import Serializer, fields

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:////tmp/quotes.db'
db = SQLAlchemy(app)

##### MODELS #####

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(80))
    last = db.Column(db.String(80))

    def __init__(self, first, last):
        self.first = first
        self.last = last

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

##### SERIALIZERS #####

class AuthorSerializer(Serializer):
    formatted_name = fields.Method("format_name")

    def format_name(self, author):
        return "%s, %s" % (author.last, author.first)

    class Meta:
        fields = ('id', 'first', 'last', "formatted_name")

class QuoteSerializer(Serializer):
    author = fields.Nested(AuthorSerializer)

    class Meta:
        fields = ("id", "content", "posted_at", 'author')

# Single serializers with no extra configuration
author_serializer = AuthorSerializer()
quote_serializer = QuoteSerializer()

##### API #####

@app.route("/api/v1/authors")
def get_authors():
    authors = Author.query.all()
    # Serialize the queryset
    serializer = AuthorSerializer(many=True)
    data, errors = serializer.dump(authors)
    if errors:
        return jsonify(errors), 400
    return jsonify({"authors": data})

@app.route("/api/v1/authors/<int:pk>")
def get_author(pk):
    try:
        author = Author.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Author could not be found."}), 400
    author_data, author_errors = author_serializer.dump(author)
    quotes_serializer = QuoteSerializer(only=('id', 'content'), many=True)
    quotes_data, quote_errors = quotes_serializer.dump(author.quotes.all())
    if author_errors:
        return jsonify(author_errors), 400
    if quote_errors:
        return jsonify(quote_errors), 400
    return jsonify({'author': author_data, 'quotes': quotes_data})

@app.route('/api/v1/quotes', methods=['GET'])
def get_quotes():
    quotes = Quote.query.all()
    serializer = QuoteSerializer(only=("id", "content"), many=True)
    data, errors = serializer.dump(quotes)
    if errors:
        return jsonify(errors), 400
    return jsonify({"quotes": data})

@app.route("/api/v1/quotes/<int:pk>")
def get_quote(pk):
    try:
        quote = Quote.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Quote could not be found."}), 400
    data, errors = quote_serializer.dump(quote)
    if errors:
        return jsonify(errors), 400
    return jsonify({"quote": data})

@app.route("/api/v1/quotes/new", methods=["POST"])
def new_quote():
    first, last = request.json['author'].split(" ")
    content = request.json['quote']
    author = Author.query.filter_by(first=first, last=last).first()
    if author is None:
        # Create a new author
        author = Author(first, last)
        db.session.add(author)
    # Create new quote
    quote = Quote(content, author)
    db.session.add(quote)
    db.session.commit()
    data, errors = quote_serializer.dump(Quote.query.get(quote.id))
    if errors:
        return jsonify(errors), 400
    return jsonify({"message": "Created new quote.",
                    "quote": data})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)
