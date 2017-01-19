from __future__ import print_function, unicode_literals

import cProfile
import gc
import timeit
import time

from marshmallow import Schema, fields, ValidationError, pre_load


# Custom validator
def must_not_be_blank(data):
    if not data:
        raise ValidationError('Data not provided.')


class AuthorSchema(Schema):
    class Meta:
        expect_object = True
        no_callable_fields = True

    id = fields.Int(dump_only=True)
    first = fields.Str()
    last = fields.Str()
    book_count = fields.Float()
    age = fields.Float()
    address = fields.Str()
    full_name = fields.Method('full_name')

    def full_name(self, obj):
        return obj.first + ' ' + obj.last

    def format_name(self, author):
        return "{0}, {1}".format(author.last, author.first)


class QuoteSchema(Schema):
    class Meta:
        expect_object = True
        no_callable_fields = True

    id = fields.Int(dump_only=True)
    author = fields.Nested(AuthorSchema, validate=must_not_be_blank)
    content = fields.Str(required=True, validate=must_not_be_blank)
    posted_at = fields.Int(dump_only=True)
    book_name = fields.Str()
    page_number = fields.Float()
    line_number = fields.Float()
    col_number = fields.Float()

    # Allow client to pass author's full name in request body
    # e.g. {"author': 'Tim Peters"} rather than {"first": "Tim", "last": "Peters"}
    @pre_load
    def process_author(self, data):
        author_name = data.get('author')
        if author_name:
            first, last = author_name.split(' ')
            author_dict = dict(first=first, last=last)
        else:
            author_dict = {}
        data['author'] = author_dict
        return data


class Author(object):
    def __init__(self, id, first, last, book_count, age, address):
        self.id = id
        self.first = first
        self.last = last
        self.book_count = book_count
        self.age = age
        self.address = address


class Quote(object):
    def __init__(self, id, author, content, posted_at, book_name, page_number,
                 line_number, col_number):
        self.id = id
        self.author = author
        self.content = content
        self.posted_at = posted_at
        self.book_name = book_name
        self.page_number = page_number
        self.line_number = line_number
        self.col_number = col_number


quotes = []
locations = []

for i in range(20):
    quotes.append(
        Quote(i, Author(i, 'Foo', 'Bar', 42, 66, '123 Fake St'),
              'Hello World', time.time(), 'The World', 34, 3, 70)
    )

def run_timeit(optimize, profile=False):
    number = 1000
    repeat = 5
    quotes_schema = QuoteSchema(many=True, optimize=optimize)
    if profile:
        profile = cProfile.Profile()
        profile.enable()

    gc.collect()
    best = min(timeit.repeat(lambda: quotes_schema.dump(quotes),
                             'gc.enable()',
                             number=number,
                             repeat=repeat))
    if profile:
        profile.disable()
        profile.dump_stats('optimized.pprof' if optimize else 'original.pprof')

    usec = best * 1e6 / number
    return usec


optimized_time = run_timeit(True)
original_time = run_timeit(False)


print('Benchmark Result:')
print('\tOriginal Time: {0:.2f} usec/dump'.format(original_time))
print('\tOptimized Time: {0:.2f} usec/dump'.format(optimized_time))
print('\tSpeed up: {0:.2f}x'.format(original_time / optimized_time))
