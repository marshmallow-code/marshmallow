# -*- coding: utf-8 -*-
"""Tests for marshmallow.validate"""
from __future__ import unicode_literals

import re
import pytest

from marshmallow.compat import PY2
from marshmallow import validate, ValidationError

@pytest.mark.parametrize('valid_url', [
    'http://example.org',
    'https://example.org',
    'ftp://example.org',
    'ftps://example.org',
    'http://example.co.jp',
    'http://www.example.com/a%C2%B1b',
    'http://www.example.com/~username/',
    'http://info.example.com/?fred',
    'http://xn--mgbh0fb.xn--kgbechtv/',
    'http://example.com/blue/red%3Fand+green',
    'http://www.example.com/?array%5Bkey%5D=value',
    'http://xn--rsum-bpad.example.org/',
    'http://123.45.67.8/',
    'http://123.45.67.8:8329/',
    'http://[2001:db8::ff00:42]:8329',
    'http://[2001::1]:8329',
    'http://www.example.com:8000/foo',
])
def test_url_absolute_valid(valid_url):
    validator = validate.URL(relative=False)
    assert validator(valid_url) == valid_url

@pytest.mark.parametrize('invalid_url', [
    'http:///example.com/',
    'https:///example.com/',
    'https://example.org\\',
    'ftp:///example.com/',
    'ftps:///example.com/',
    'http//example.org',
    'http:///',
    'http:/example.org',
    'foo://example.org',
    '../icons/logo.gif',
    'http://2001:db8::ff00:42:8329',
    'http://[192.168.1.1]:8329',
    'abc',
    '..',
    '/',
    ' ',
    '',
    None,
])
def test_url_absolute_invalid(invalid_url):
    validator = validate.URL(relative=False)
    with pytest.raises(ValidationError):
        validator(invalid_url)

@pytest.mark.parametrize('valid_url', [
    'http://example.org',
    'http://123.45.67.8/',
    'http://example.com/foo/bar/../baz',
    'https://example.com/../icons/logo.gif',
    'http://example.com/./icons/logo.gif',
    'ftp://example.com/../../../../g',
    'http://example.com/g?y/./x',
])
def test_url_relative_valid(valid_url):
    validator = validate.URL(relative=True)
    assert validator(valid_url) == valid_url

@pytest.mark.parametrize('invalid_url', [
    'http//example.org',
    'suppliers.html',
    '../icons/logo.gif',
    '\icons/logo.gif',
    '../.../g',
    '...',
    '\\',
    ' ',
    '',
    None,
])
def test_url_relative_invalid(invalid_url):
    validator = validate.URL(relative=True)
    with pytest.raises(ValidationError):
        validator(invalid_url)

@pytest.mark.parametrize('valid_url', [
    'http://example.org',
    'http://123.45.67.8/',
    'http://example',
    'http://example.',
    'http://example:80',
    'http://user.name:pass.word@example',
    'http://example/foo/bar',
])
def test_url_dont_require_tld_valid(valid_url):
    validator = validate.URL(require_tld=False)
    assert validator(valid_url) == valid_url

@pytest.mark.parametrize('invalid_url', [
    'http//example',
    'http://.example.org',
    'http:///foo/bar',
    'http:// /foo/bar',
    '',
    None,
])
def test_url_dont_require_tld_invalid(invalid_url):
    validator = validate.URL(require_tld=False)
    with pytest.raises(ValidationError):
        validator(invalid_url)

def test_url_custom_scheme():
    validator = validate.URL()
    # By default, ws not allowed
    url = 'ws://test.test'
    with pytest.raises(ValidationError):
        validator(url)

    validator = validate.URL(schemes=set(['http', 'https', 'ws']))
    assert validator(url) == url

def test_url_relative_and_custom_schemes():
    validator = validate.URL(relative=True)
    # By default, ws not allowed
    url = 'ws://test.test'
    with pytest.raises(ValidationError):
        validator(url)

    validator = validate.URL(relative=True, schemes=set(['http', 'https', 'ws']))
    assert validator(url) == url

def test_url_custom_message():
    validator = validate.URL(error="{input} ain't an URL")
    with pytest.raises(ValidationError) as excinfo:
        validator('invalid')
    assert "invalid ain't an URL" in str(excinfo)

def test_url_repr():
    assert (
        repr(validate.URL(relative=False, error=None)) ==
        '<URL(relative=False, error={0!r})>'
        .format('Not a valid URL.')
    )
    assert (
        repr(validate.URL(relative=True, error='foo')) ==
        '<URL(relative=True, error={0!r})>'
        .format('foo')
    )


@pytest.mark.parametrize('valid_email', [
    'niceandsimple@example.com',
    'NiCeAnDsImPlE@eXaMpLe.CoM',
    'very.common@example.com',
    'a.little.lengthy.but.fine@a.iana-servers.net',
    'disposable.style.email.with+symbol@example.com',
    '"very.unusual.@.unusual.com"@example.com',
    "!#$%&'*+-/=?^_`{}|~@example.org",
    'niceandsimple@[64.233.160.0]',
    'niceandsimple@localhost',
    u'josé@blah.com',
    u'δοκ.ιμή@παράδειγμα.δοκιμή',
])
def test_email_valid(valid_email):
    validator = validate.Email()
    assert validator(valid_email) == valid_email

@pytest.mark.parametrize('invalid_email', [
    'a"b(c)d,e:f;g<h>i[j\\k]l@example.com',
    'just"not"right@example.com',
    'this is"not\allowed@example.com',
    'this\\ still\\"not\\\\allowed@example.com',
    '"much.more unusual"@example.com',
    '"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com',
    '" "@example.org',
    'user@example',
    '@nouser.com',
    'example.com',
    'user',
    '',
    None,
])
def test_email_invalid(invalid_email):
    validator = validate.Email()
    with pytest.raises(ValidationError):
        validator(invalid_email)

def test_email_custom_message():
    validator = validate.Email(error='{input} is not an email addy.')
    with pytest.raises(ValidationError) as excinfo:
        validator('invalid')
    assert 'invalid is not an email addy.' in str(excinfo)

def test_email_repr():
    assert (
        repr(validate.Email(error=None)) ==
        '<Email(error={0!r})>'
        .format('Not a valid email address.')
    )
    assert (
        repr(validate.Email(error='foo')) ==
        '<Email(error={0!r})>'
        .format('foo')
    )


def test_range_min():
    assert validate.Range(1, 2)(1) == 1
    assert validate.Range(0)(1) == 1
    assert validate.Range()(1) == 1
    assert validate.Range(1, 1)(1) == 1

    with pytest.raises(ValidationError):
        validate.Range(2, 3)(1)
    with pytest.raises(ValidationError):
        validate.Range(2)(1)

def test_range_max():
    assert validate.Range(1, 2)(2) == 2
    assert validate.Range(None, 2)(2) == 2
    assert validate.Range()(2) == 2
    assert validate.Range(2, 2)(2) == 2

    with pytest.raises(ValidationError):
        validate.Range(0, 1)(2)
    with pytest.raises(ValidationError):
        validate.Range(None, 1)(2)

def test_range_custom_message():
    v = validate.Range(2, 3, error='{input} is not between {min} and {max}')
    with pytest.raises(ValidationError) as excinfo:
        v(1)
    assert '1 is not between 2 and 3' in str(excinfo)

    v = validate.Range(2, None, error='{input} is less than {min}')
    with pytest.raises(ValidationError) as excinfo:
        v(1)
    assert '1 is less than 2' in str(excinfo)

    v = validate.Range(None, 3, error='{input} is greater than {max}')
    with pytest.raises(ValidationError) as excinfo:
        v(4)
    assert '4 is greater than 3' in str(excinfo)

def test_range_repr():
    assert (
        repr(validate.Range(min=None, max=None, error=None)) ==
        '<Range(min=None, max=None, error=None)>'
    )
    assert (
        repr(validate.Range(min=1, max=3, error='foo')) ==
        '<Range(min=1, max=3, error={0!r})>'
        .format('foo')
    )


def test_length_min():
    assert validate.Length(3, 5)('foo') == 'foo'
    assert validate.Length(3, 5)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(0)('a') == 'a'
    assert validate.Length(0)([1]) == [1]
    assert validate.Length()('') == ''
    assert validate.Length()([]) == []
    assert validate.Length(1, 1)('a') == 'a'
    assert validate.Length(1, 1)([1]) == [1]

    with pytest.raises(ValidationError):
        validate.Length(4, 5)('foo')
    with pytest.raises(ValidationError):
        validate.Length(4, 5)([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Length(5)('foo')
    with pytest.raises(ValidationError):
        validate.Length(5)([1, 2, 3])

def test_length_max():
    assert validate.Length(1, 3)('foo') == 'foo'
    assert validate.Length(1, 3)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(None, 1)('a') == 'a'
    assert validate.Length(None, 1)([1]) == [1]
    assert validate.Length()('') == ''
    assert validate.Length()([]) == []
    assert validate.Length(2, 2)('ab') == 'ab'
    assert validate.Length(2, 2)([1, 2]) == [1, 2]

    with pytest.raises(ValidationError):
        validate.Length(1, 2)('foo')
    with pytest.raises(ValidationError):
        validate.Length(1, 2)([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Length(None, 2)('foo')
    with pytest.raises(ValidationError):
        validate.Length(None, 2)([1, 2, 3])

def test_length_equal():
    assert validate.Length(equal=3)('foo') == 'foo'
    assert validate.Length(equal=3)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(equal=None)('') == ''
    assert validate.Length(equal=None)([]) == []

    with pytest.raises(ValidationError):
        validate.Length(equal=2)('foo')
    with pytest.raises(ValidationError):
        validate.Length(equal=2)([1, 2, 3])

    with pytest.raises(ValueError):
        validate.Length(1, None, equal=3)('foo')
    with pytest.raises(ValueError):
        validate.Length(None, 5, equal=3)('foo')
    with pytest.raises(ValueError):
        validate.Length(1, 5, equal=3)('foo')

def test_length_custom_message():
    v = validate.Length(5, 6, error='{input} is not between {min} and {max}')
    with pytest.raises(ValidationError) as excinfo:
        v('foo')
    assert 'foo is not between 5 and 6' in str(excinfo)

    v = validate.Length(5, None, error='{input} is shorter than {min}')
    with pytest.raises(ValidationError) as excinfo:
        v('foo')
    assert 'foo is shorter than 5' in str(excinfo)

    v = validate.Length(None, 2, error='{input} is longer than {max}')
    with pytest.raises(ValidationError) as excinfo:
        v('foo')
    assert 'foo is longer than 2' in str(excinfo)

    v = validate.Length(None, None, equal=4, error='{input} does not have {equal}')
    with pytest.raises(ValidationError) as excinfo:
        v('foo')
    assert 'foo does not have 4' in str(excinfo)

def test_length_repr():
    assert (
        repr(validate.Length(min=None, max=None, error=None, equal=None)) ==
        '<Length(min=None, max=None, equal=None, error=None)>'
    )
    assert (
        repr(validate.Length(min=1, max=3, error='foo', equal=None)) ==
        '<Length(min=1, max=3, equal=None, error={0!r})>'
        .format('foo')
    )
    assert (
        repr(validate.Length(min=None, max=None, error='foo', equal=5)) ==
        '<Length(min=None, max=None, equal=5, error={0!r})>'
        .format('foo')
    )


def test_equal():
    assert validate.Equal('a')('a') == 'a'
    assert validate.Equal(1)(1) == 1
    assert validate.Equal([1])([1]) == [1]

    with pytest.raises(ValidationError):
        validate.Equal('b')('a')
    with pytest.raises(ValidationError):
        validate.Equal(2)(1)
    with pytest.raises(ValidationError):
        validate.Equal([2])([1])

def test_equal_custom_message():
    v = validate.Equal('a', error='{input} is not equal to {other}.')
    with pytest.raises(ValidationError) as excinfo:
        v('b')
    assert 'b is not equal to a.' in str(excinfo)

def test_equal_repr():
    assert (
        repr(validate.Equal(comparable=123, error=None)) ==
        '<Equal(comparable=123, error={0!r})>'
        .format('Must be equal to {other}.')
    )
    assert (
        repr(validate.Equal(comparable=123, error='foo')) ==
        '<Equal(comparable=123, error={0!r})>'
        .format('foo')
    )


def test_regexp_str():
    assert validate.Regexp(r'a')('a') == 'a'
    assert validate.Regexp(r'\w')('_') == '_'
    assert validate.Regexp(r'\s')(' ') == ' '
    assert validate.Regexp(r'1')('1') == '1'
    assert validate.Regexp(r'[0-9]+')('1') == '1'
    assert validate.Regexp(r'a', re.IGNORECASE)('A') == 'A'

    with pytest.raises(ValidationError):
        validate.Regexp(r'[0-9]+')('a')
    with pytest.raises(ValidationError):
        validate.Regexp(r'[a-z]+')('1')
    with pytest.raises(ValidationError):
        validate.Regexp(r'a')('A')

def test_regexp_compile():
    assert validate.Regexp(re.compile(r'a'))('a') == 'a'
    assert validate.Regexp(re.compile(r'\w'))('_') == '_'
    assert validate.Regexp(re.compile(r'\s'))(' ') == ' '
    assert validate.Regexp(re.compile(r'1'))('1') == '1'
    assert validate.Regexp(re.compile(r'[0-9]+'))('1') == '1'
    assert validate.Regexp(re.compile(r'a', re.IGNORECASE))('A') == 'A'
    assert validate.Regexp(re.compile(r'a', re.IGNORECASE), re.IGNORECASE)('A') == 'A'

    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'[0-9]+'))('a')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'[a-z]+'))('1')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'a'))('A')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'a'), re.IGNORECASE)('A')

def test_regexp_custom_message():
    rex = r'[0-9]+'
    v = validate.Regexp(rex, error='{input} does not match {regex}')
    with pytest.raises(ValidationError) as excinfo:
        v('a')
    assert 'a does not match [0-9]+' in str(excinfo)

def test_regexp_repr():
    assert (
        repr(validate.Regexp(regex='abc', flags=0, error=None)) ==
        '<Regexp(regex={0!r}, error={1!r})>'
        .format(re.compile('abc'), 'String does not match expected pattern.')
    )
    assert (
        repr(validate.Regexp(regex='abc', flags=re.IGNORECASE, error='foo')) ==
        '<Regexp(regex={0!r}, error={1!r})>'
        .format(re.compile('abc', re.IGNORECASE), 'foo')
    )


def test_predicate():
    class Dummy(object):
        def _true(self):
            return True

        def _false(self):
            return False

        def _list(self):
            return [1, 2, 3]

        def _empty(self):
            return []

        def _identity(self, arg):
            return arg

    d = Dummy()

    assert validate.Predicate('_true')(d) == d
    assert validate.Predicate('_list')(d) == d
    assert validate.Predicate('_identity', arg=True)(d) == d
    assert validate.Predicate('_identity', arg=1)(d) == d
    assert validate.Predicate('_identity', arg='abc')(d) == d

    with pytest.raises(ValidationError) as excinfo:
        validate.Predicate('_false')(d)
    assert 'Invalid input.' in str(excinfo)
    with pytest.raises(ValidationError):
        validate.Predicate('_empty')(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg=False)(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg=0)(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg='')(d)

def test_predicate_custom_message():
    class Dummy(object):
        def _false(self):
            return False

        def __str__(self):
            return 'Dummy'
    d = Dummy()
    with pytest.raises(ValidationError) as excinfo:
        validate.Predicate('_false', error='{input}.{method} is invalid!')(d)
    assert 'Dummy._false is invalid!' in str(excinfo)

def test_predicate_repr():
    assert (
        repr(validate.Predicate(method='foo', error=None)) ==
        '<Predicate(method={0!r}, kwargs={1!r}, error={2!r})>'
        .format('foo', {}, 'Invalid input.')
    )
    assert (
        repr(validate.Predicate(method='foo', error='bar', zoo=1)) ==
        '<Predicate(method={0!r}, kwargs={1!r}, error={2!r})>'
        .format('foo', {str('zoo') if PY2 else 'zoo': 1}, 'bar')
    )


def test_noneof():
    assert validate.NoneOf([1, 2, 3])(4) == 4
    assert validate.NoneOf('abc')('d') == 'd'
    assert validate.NoneOf('')([]) == []
    assert validate.NoneOf([])('') == ''
    assert validate.NoneOf([])([]) == []
    assert validate.NoneOf([1, 2, 3])(None) is None

    with pytest.raises(ValidationError) as excinfo:
        validate.NoneOf([1, 2, 3])(3)
    assert 'Invalid input.' in str(excinfo)
    with pytest.raises(ValidationError):
        validate.NoneOf('abc')('c')
    with pytest.raises(ValidationError):
        validate.NoneOf([1, 2, None])(None)
    with pytest.raises(ValidationError):
        validate.NoneOf('')('')

def test_noneof_custom_message():
    with pytest.raises(ValidationError) as excinfo:
        validate.NoneOf([1, 2], error='<not valid>')(1)
    assert '<not valid>' in str(excinfo)

    none_of = validate.NoneOf(
        [1, 2],
        error='{input} cannot be one of {values}'
    )
    with pytest.raises(ValidationError) as excinfo:
        none_of(1)
    assert '1 cannot be one of 1, 2' in str(excinfo)

def test_noneof_repr():
    assert (
        repr(validate.NoneOf(iterable=[1, 2, 3], error=None)) ==
        '<NoneOf(iterable=[1, 2, 3], error={0!r})>'
        .format('Invalid input.')
    )
    assert (
        repr(validate.NoneOf(iterable=[1, 2, 3], error='foo')) ==
        '<NoneOf(iterable=[1, 2, 3], error={0!r})>'
        .format('foo')
    )


def test_oneof():
    assert validate.OneOf([1, 2, 3])(2) == 2
    assert validate.OneOf('abc')('b') == 'b'
    assert validate.OneOf('')('') == ''
    assert validate.OneOf(dict(a=0, b=1))('a') == 'a'
    assert validate.OneOf((1, 2, None))(None) is None

    with pytest.raises(ValidationError) as excinfo:
        validate.OneOf([1, 2, 3])(4)
    assert 'Not a valid choice.' in str(excinfo)
    with pytest.raises(ValidationError):
        validate.OneOf('abc')('d')
    with pytest.raises(ValidationError):
        validate.OneOf((1, 2, 3))(None)
    with pytest.raises(ValidationError):
        validate.OneOf([])([])
    with pytest.raises(ValidationError):
        validate.OneOf(())(())
    with pytest.raises(ValidationError):
        validate.OneOf(dict(a=0, b=1))(0)
    with pytest.raises(ValidationError):
        validate.OneOf('123')(1)

def test_oneof_options():
    oneof = validate.OneOf([1, 2, 3], ['one', 'two', 'three'])
    expected = [('1', 'one'), ('2', 'two'), ('3', 'three')]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2, 3], ['one', 'two'])
    expected = [('1', 'one'), ('2', 'two'), ('3', '')]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2], ['one', 'two', 'three'])
    expected = [('1', 'one'), ('2', 'two'), ('', 'three')]
    assert list(oneof.options()) == expected

    oneof = validate.OneOf([1, 2])
    expected = [('1', ''), ('2', '')]
    assert list(oneof.options()) == expected

def test_oneof_text():
    oneof = validate.OneOf([1, 2, 3], ['one', 'two', 'three'])
    assert oneof.choices_text == '1, 2, 3'
    assert oneof.labels_text == 'one, two, three'

    oneof = validate.OneOf([1], ['one'])
    assert oneof.choices_text == '1'
    assert oneof.labels_text == 'one'

    oneof = validate.OneOf(dict(a=0, b=1))
    assert ', '.join(sorted(oneof.choices_text.split(', '))) == 'a, b'
    assert oneof.labels_text == ''

def test_oneof_custom_message():
    oneof = validate.OneOf([1, 2, 3], error='{input} is not one of {choices}')
    expected = '4 is not one of 1, 2, 3'
    with pytest.raises(ValidationError):
        oneof(4)
    assert expected in str(expected)

    oneof = validate.OneOf([1, 2, 3],
        ['one', 'two', 'three'],
        error='{input} is not one of {labels}'
    )
    expected = '4 is not one of one, two, three'
    with pytest.raises(ValidationError):
        oneof(4)
    assert expected in str(expected)

def test_oneof_repr():
    assert (
        repr(validate.OneOf(choices=[1, 2, 3], labels=None, error=None)) ==
        '<OneOf(choices=[1, 2, 3], labels=[], error={0!r})>'
        .format('Not a valid choice.')
    )
    assert (
        repr(validate.OneOf(choices=[1, 2, 3], labels=['a', 'b', 'c'], error='foo')) ==
        '<OneOf(choices=[1, 2, 3], labels={0!r}, error={1!r})>'
        .format(['a', 'b', 'c'], 'foo')
    )


def test_containsonly_in_list():
    assert validate.ContainsOnly([])([]) == []
    assert validate.ContainsOnly([1, 2, 3])([1]) == [1]
    assert validate.ContainsOnly([1, 1, 2])([1, 1]) == [1, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2]) == [1, 2]
    assert validate.ContainsOnly([1, 2, 3])([2, 1]) == [2, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2, 3]) == [1, 2, 3]
    assert validate.ContainsOnly([1, 2, 3])([3, 1, 2]) == [3, 1, 2]
    assert validate.ContainsOnly([1, 2, 3])([2, 3, 1]) == [2, 3, 1]
    assert validate.ContainsOnly([1, 2, 3])([1, 2, 3, 1]) == [1, 2, 3, 1]
    assert validate.ContainsOnly([1, 2, 3])([]) == []

    with pytest.raises(ValidationError):
        validate.ContainsOnly([1, 2, 3])([4])
    with pytest.raises(ValidationError):
        validate.ContainsOnly([])([1])

def test_contains_only_unhashable_types():
    assert validate.ContainsOnly([[1], [2], [3]])([[1]]) == [[1]]
    assert validate.ContainsOnly([[1], [1], [2]])([[1], [1]]) == [[1], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([[1], [2]]) == [[1], [2]]
    assert validate.ContainsOnly([[1], [2], [3]])([[2], [1]]) == [[2], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([[1], [2], [3]]) == [[1], [2], [3]]
    assert validate.ContainsOnly([[1], [2], [3]])([[3], [1], [2]]) == [[3], [1], [2]]
    assert validate.ContainsOnly([[1], [2], [3]])([[2], [3], [1]]) == [[2], [3], [1]]
    assert validate.ContainsOnly([[1], [2], [3]])([]) == []

    with pytest.raises(ValidationError):
        validate.ContainsOnly([[1], [2], [3]])([[4]])
    with pytest.raises(ValidationError):
        validate.ContainsOnly([])([1])

def test_containsonly_in_tuple():
    assert validate.ContainsOnly(())(()) == ()
    assert validate.ContainsOnly((1, 2, 3))((1,)) == (1,)
    assert validate.ContainsOnly((1, 1, 2))((1, 1)) == (1, 1)
    assert validate.ContainsOnly((1, 2, 3))((1, 2)) == (1, 2)
    assert validate.ContainsOnly((1, 2, 3))((2, 1)) == (2, 1)
    assert validate.ContainsOnly((1, 2, 3))((1, 2, 3)) == (1, 2, 3)
    assert validate.ContainsOnly((1, 2, 3))((3, 1, 2)) == (3, 1, 2)
    assert validate.ContainsOnly((1, 2, 3))((2, 3, 1)) == (2, 3, 1)
    assert validate.ContainsOnly((1, 2, 3))(()) == tuple()
    with pytest.raises(ValidationError):
        validate.ContainsOnly((1, 2, 3))((4,))
    with pytest.raises(ValidationError):
        validate.ContainsOnly(())((1,))


def test_contains_only_in_string():
    assert validate.ContainsOnly('')('') == ''
    assert validate.ContainsOnly('abc')('a') == 'a'
    assert validate.ContainsOnly('aab')('aa') == 'aa'
    assert validate.ContainsOnly('abc')('ab') == 'ab'
    assert validate.ContainsOnly('abc')('ba') == 'ba'
    assert validate.ContainsOnly('abc')('abc') == 'abc'
    assert validate.ContainsOnly('abc')('cab') == 'cab'
    assert validate.ContainsOnly('abc')('bca') == 'bca'
    assert validate.ContainsOnly('abc')('') == ''

    with pytest.raises(ValidationError):
        validate.ContainsOnly('abc')('d')
    with pytest.raises(ValidationError):
        validate.ContainsOnly('')('a')


def test_containsonly_custom_message():
    containsonly = validate.ContainsOnly(
        [1, 2, 3],
        error='{input} is not one of {choices}'
    )
    expected = '4, 5 is not one of 1, 2, 3'
    with pytest.raises(ValidationError):
        containsonly([4, 5])
    assert expected in str(expected)

    containsonly = validate.ContainsOnly([1, 2, 3],
        ['one', 'two', 'three'],
        error='{input} is not one of {labels}'
    )
    expected = '4, 5 is not one of one, two, three'
    with pytest.raises(ValidationError):
        containsonly([4, 5])
    assert expected in str(expected)

def test_containsonly_repr():
    assert (
        repr(validate.ContainsOnly(choices=[1, 2, 3], labels=None, error=None)) ==
        '<ContainsOnly(choices=[1, 2, 3], labels=[], error={0!r})>'
        .format('One or more of the choices you made was not acceptable.')
    )
    assert (
        repr(validate.ContainsOnly(choices=[1, 2, 3], labels=['a', 'b', 'c'], error='foo')) ==
        '<ContainsOnly(choices=[1, 2, 3], labels={0!r}, error={1!r})>'
        .format(['a', 'b', 'c'], 'foo')
    )
