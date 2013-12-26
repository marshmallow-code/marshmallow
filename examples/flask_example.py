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

##### API #####

@app.route("/api/v1/authors")
def get_authors():
    authors = Author.query.all()
    # Serialize the queryset
    return jsonify({"authors": AuthorSerializer(authors, many=True).data})

@app.route("/api/v1/authors/<int:pk>")
def get_author(pk):
    try:
        author = Author.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Author could not be found."}), 400
    return jsonify({"author": AuthorSerializer(author).data,
                    "quotes": QuoteSerializer(author.quotes.all(),
                                                only=('id', 'content')).data})

@app.route("/api/v1/quotes", methods=["GET"])
def get_quotes():
    quotes = Quote.query.all()
    serialized = QuoteSerializer(quotes, only=("id", "content"), many=True)
    return jsonify({"quotes": serialized.data})

@app.route("/api/v1/quotes/<int:pk>")
def get_quote(pk):
    try:
        quote = Quote.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Quote could not be found."}), 400
    return jsonify({"quote": QuoteSerializer(quote).data})

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
    return jsonify({"message": "Created new quote.",
                    "quote": QuoteSerializer(Quote.query.get(quote.id)).data})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)
