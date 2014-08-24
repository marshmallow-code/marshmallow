from bottle import route, request, run
from textblob import TextBlob
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

blob_serializer = BlobSerializer()

@route("/api/v1/analyze", method="POST")
def analyze():
    blob = TextBlob(request.json['text'])
    result = blob_serializer.dump(blob)
    return result.data


run(reloader=True, port=5000)
