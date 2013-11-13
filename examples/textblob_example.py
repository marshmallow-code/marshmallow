# -*- coding: utf-8 -*-
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


class WordSerializer(Serializer):
    lemma = fields.String()
    definitions = fields.List(fields.String)
    singular = fields.Function(lambda obj: obj.singularize())
    plural = fields.Function(lambda obj: obj.pluralize())


@route("/api/v1/analyze", method="POST")
def analyze():
    blob = TextBlob(request.json['text'])
    return BlobSerializer(blob).data

@route("/api/v1/word/<word>", method="POST")
def analyze_word(word):
    w = Word(word)
    return WordSerializer(w).data

run(port=5000)
