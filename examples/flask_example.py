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
        return "{}, {}".format(author.last, author.first)

    class Meta:
        fields = ('id', 'first', 'last', "formatted_name")

class QuoteSerializer(Serializer):
    author = fields.Nested(AuthorSerializer)

    class Meta:
        fields = ("id", "content", "posted_at", 'author')

class SchemaError(Exception):
    """Error that is raised when a marshalling or umarshalling error occurs.
    Stores the dictionary of validation errors that occurred.
    """
    def __init__(self, message, errors):
        Exception.__init__(self, message)
        self.errors = errors

# When a marshalling/unmarshalling error occurs, raise a SchemaError
@AuthorSerializer.error_handler
@QuoteSerializer.error_handler
def handle_errors(serializer, errors, obj):
    raise SchemaError('There was a problem marshalling or unmarshalling {}'
            .format(obj), errors=errors)

author_serializer = AuthorSerializer()
quote_serializer = QuoteSerializer()
quotes_serializer = QuoteSerializer(many=True, only=('id', 'content'))

##### API #####

@app.errorhandler(SchemaError)
def handle_marshalling_error(err):
    """When a `SchemaError` is raised, return a 400 response with the
    jsonified error dictionary.
    """
    return jsonify(err.errors), 400

@app.route("/api/v1/authors")
def get_authors():
    authors = Author.query.all()
    # Serialize the queryset
    serializer = AuthorSerializer(many=True)
    result = serializer.dump(authors)
    return jsonify({"authors": result.data})

@app.route("/api/v1/authors/<int:pk>")
def get_author(pk):
    try:
        author = Author.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Author could not be found."}), 400
    author_result = author_serializer.dump(author)
    quotes_result = quotes_serializer.dump(author.quotes.all())
    return jsonify({'author': author_result.data, 'quotes': quotes_result.data})

@app.route('/api/v1/quotes', methods=['GET'])
def get_quotes():
    quotes = Quote.query.all()
    result = quotes_serializer.dump(quotes)
    return jsonify({"quotes": result.data})

@app.route("/api/v1/quotes/<int:pk>")
def get_quote(pk):
    try:
        quote = Quote.query.get(pk)
    except IntegrityError:
        return jsonify({"message": "Quote could not be found."}), 400
    result = quote_serializer.dump(quote)
    return jsonify({"quote": result.data})

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
    result = quote_serializer.dump(Quote.query.get(quote.id))
    return jsonify({"message": "Created new quote.",
                    "quote": result.data})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, port=5000)
