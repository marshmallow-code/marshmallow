# -*- coding: utf-8 -*-
import re
import pytest

from marshmallow import validate, ValidationError

def test_url_absolute():
    validator = validate.URL(relative=False)

    valid_urls = (
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
        'http://2001:db8::ff00:42:8329',
        'http://www.example.com:8000/foo',
    )

    for valid_url in valid_urls:
        assert validator(valid_url) == valid_url

    invalid_urls = (
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
        'abc',
        '..',
        ' ',
        '/'
        '',
    )

    for invalid_url in invalid_urls:
        with pytest.raises(ValidationError):
            validator(invalid_url)

    assert validator(None) is None

def test_url_relative():
    validator = validate.URL(relative=True)

    valid_urls = (
        'http://example.org',
        'http://123.45.67.8/',
        'http://example.com/foo/bar/../baz',
        'https://example.com/../icons/logo.gif',
        'http://example.com/./icons/logo.gif',
        'ftp://example.com/../../../../g',
        'http://example.com/g?y/./x',
        '',
    )

    for valid_url in valid_urls:
        assert validator(valid_url) == valid_url

    invalid_urls = (
        'http//example.org',
        'suppliers.html',
        '../icons/logo.gif',
        '\icons/logo.gif',
        '../.../g',
        '...',
        '\\',
        ' ',
    )

    for invalid_url in invalid_urls:
        with pytest.raises(ValidationError):
            validator(invalid_url)

    assert validator(None) is None

def test_email():
    validator = validate.Email()

    valid_emails = (
        'niceandsimple@example.com',
        'NiCeAnDsImPlE@eXaMpLe.CoM',
        'very.common@example.com',
        'a.little.lengthy.but.fine@a.iana-servers.net',
        'disposable.style.email.with+symbol@example.com',
        '"very.unusual.@.unusual.com"@example.com',
        "!#$%&'*+-/=?^_`{}|~@example.org",
        'niceandsimple@[64.233.160.0]',
        'niceandsimple@localhost',
    )

    for valid_email in valid_emails:
        assert validator(valid_email) == valid_email

    invalid_emails = (
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
    )

    for invalid_email in invalid_emails:
        with pytest.raises(ValidationError):
            validator(invalid_email)

    assert validator(None) is None

def test_range_min():
    assert validate.Range(1, 2)(1) == 1
    assert validate.Range(0)(1) == 1
    assert validate.Range()(1) == 1
    assert validate.Range(1, 1)(1) == 1
    assert validate.Range(0)(None) is None

    with pytest.raises(ValidationError):
        validate.Range(2, 3)(1)
    with pytest.raises(ValidationError):
        validate.Range(2)(1)

def test_range_max():
    assert validate.Range(1, 2)(2) == 2
    assert validate.Range(None, 2)(2) == 2
    assert validate.Range()(2) == 2
    assert validate.Range(2, 2)(2) == 2
    assert validate.Range(None, 2)(None) is None

    with pytest.raises(ValidationError):
        validate.Range(0, 1)(2)
    with pytest.raises(ValidationError):
        validate.Range(None, 1)(2)

def test_length_min():
    assert validate.Length(3, 5)('foo') == 'foo'
    assert validate.Length(3, 5)([1, 2, 3]) == [1, 2, 3]
    assert validate.Length(0)('a') == 'a'
    assert validate.Length(0)([1]) == [1]
    assert validate.Length()('') == ''
    assert validate.Length()([]) == []
    assert validate.Length(1, 1)('a') == 'a'
    assert validate.Length(1, 1)([1]) == [1]
    assert validate.Length(0)(None) is None

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
    assert validate.Length(None, 2)(None) is None

    with pytest.raises(ValidationError):
        validate.Length(1, 2)('foo')
    with pytest.raises(ValidationError):
        validate.Length(1, 2)([1, 2, 3])
    with pytest.raises(ValidationError):
        validate.Length(None, 2)('foo')
    with pytest.raises(ValidationError):
        validate.Length(None, 2)([1, 2, 3])

def test_equal():
    assert validate.Equal('a')('a') == 'a'
    assert validate.Equal(1)(1) == 1
    assert validate.Equal([1])([1]) == [1]

    assert validate.Equal('a')(None) is None
    assert validate.Equal(1)(None) is None
    assert validate.Equal([1])(None) is None
    assert validate.Equal(None)(None) is None

    with pytest.raises(ValidationError):
        validate.Equal('b')('a')
    with pytest.raises(ValidationError):
        validate.Equal(2)(1)
    with pytest.raises(ValidationError):
        validate.Equal([2])([1])

def test_regexp_str():
    assert validate.Regexp(r'a')('a') == 'a'
    assert validate.Regexp(r'\w')('_') == '_'
    assert validate.Regexp(r'\s')(' ') == ' '
    assert validate.Regexp(r'1')('1') == '1'
    assert validate.Regexp(r'[0-9]+')('1') == '1'
    assert validate.Regexp(r'a', re.IGNORECASE)('A') == 'A'

    assert validate.Regexp(r'a')(None) is None
    assert validate.Regexp(r'a', re.IGNORECASE)(None) is None

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

    assert validate.Regexp(re.compile(r'a'))(None) is None
    assert validate.Regexp(re.compile(r'a', re.IGNORECASE))(None) is None

    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'[0-9]+'))('a')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'[a-z]+'))('1')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'a'))('A')
    with pytest.raises(ValidationError):
        validate.Regexp(re.compile(r'a'), re.IGNORECASE)('A')

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

    assert validate.Predicate('_true')(None) is None
    assert validate.Predicate('_false')(None) is None
    assert validate.Predicate('_identity', arg=True)(None) is None
    assert validate.Predicate('_identity', arg=False)(None) is None

    with pytest.raises(ValidationError):
        validate.Predicate('_false')(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_empty')(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg=False)(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg=0)(d)
    with pytest.raises(ValidationError):
        validate.Predicate('_identity', arg='')(d)

def test_function():
    def dummy1(foo):
        return foo

    def dummy2(foo, bar):
        return foo + bar

    assert validate.Function(dummy1)(True) == True
    assert validate.Function(dummy1)(1) == 1
    assert validate.Function(dummy1)([1, 2]) == [1, 2]
    assert validate.Function(dummy1)(None) is None

    assert validate.Function(dummy2, bar=1)(0) == 0
    assert validate.Function(dummy2, bar=[1, 2])([]) == []
    assert validate.Function(dummy2, bar=1)(None) is None
    assert validate.Function(dummy2, bar=[1, 2])(None) is None

    with pytest.raises(ValidationError):
        validate.Function(dummy1)(False)
    with pytest.raises(ValidationError):
        validate.Function(dummy1)(0)
    with pytest.raises(ValidationError):
        validate.Function(dummy1)([])
    with pytest.raises(ValidationError):
        validate.Function(dummy1)('')
    with pytest.raises(ValidationError):
        validate.Function(dummy1)('abc')

    with pytest.raises(ValidationError):
        validate.Function(dummy2, bar=-1)(1)
    with pytest.raises(ValidationError):
        validate.Function(dummy2, bar=[])([])
    with pytest.raises(ValidationError):
        validate.Function(dummy2, bar='')('')
    with pytest.raises(ValidationError):
        validate.Function(dummy2, bar='abc')('')

def test_noneof():
    assert validate.NoneOf([1, 2, 3])(4) == 4
    assert validate.NoneOf('abc')('d') == 'd'
    assert validate.NoneOf((i for i in [1, 2]))(3) == 3
    assert validate.NoneOf('')([]) == []
    assert validate.NoneOf([])('') == ''
    assert validate.NoneOf('')('') == ''
    assert validate.NoneOf([])([]) == []
    assert validate.NoneOf([1, 2, 3])(None) is None

    with pytest.raises(ValidationError):
        validate.NoneOf([1, 2, 3])(3)
    with pytest.raises(ValidationError):
        validate.NoneOf('abc')('c')
    with pytest.raises(ValidationError):
        validate.NoneOf((i for i in [1, 2]))(2)
