# -*- coding: utf-8 -*-
import pytest

from marshmallow import validate, ValidationError

def test_invalid_email():
    invalid1 = "user@example"
    with pytest.raises(ValidationError):
        validate.email(invalid1)
    invalid2 = "example.com"
    with pytest.raises(ValidationError):
        validate.email(invalid2)
    invalid3 = "user"
    with pytest.raises(ValidationError):
        validate.email(invalid3)
    with pytest.raises(ValidationError):
        validate.email('@nouser.com')

def test_validate_email_none():
    assert validate.email(None) is None

def test_validate_url_none():
    assert validate.url(None) is None

def test_min_length():
    with pytest.raises(ValidationError):
        validate.length('foo', 4, 5)
    assert validate.length('foo', 3, 5) == 'foo'
    with pytest.raises(ValidationError):
        validate.length([1, 2, 3], 4, 5)
    assert validate.length([1, 2, 3], 3, 5) == [1, 2, 3]
    with pytest.raises(ValidationError):
        validate.length('foo', 5)

def test_max_length():
    with pytest.raises(ValidationError):
        validate.length('foo', 1, 2)
    assert validate.length('foo', 1, 3) == 'foo'
    with pytest.raises(ValidationError):
        validate.length([1, 2, 3], 1, 2)
    assert validate.length([1, 2, 3], 1, 3) == [1, 2, 3]
    with pytest.raises(ValidationError):
        validate.length('foo', None, 2)

def test_validate_length_none():
    assert validate.length(None) is None

def test_min_ranging():
    with pytest.raises(ValidationError):
        validate.ranging(1, 2, 3)
    assert validate.ranging(1, 1, 2) == 1
    with pytest.raises(ValidationError):
        validate.ranging(1, 2)

def test_max_ranging():
    with pytest.raises(ValidationError):
        validate.ranging(2, 0, 1)
    assert validate.ranging(2, 1, 2) == 2
    with pytest.raises(ValidationError):
        validate.ranging(2, None, 1)

def test_validate_ranging_none():
    assert validate.ranging(None) is None

def test_equal():
    assert validate.equal('a', 'a') == 'a'
    assert validate.equal(1, 1) == 1
    assert validate.ranging(None, None) is None
    assert validate.ranging(None, 'a') is None
    assert validate.ranging(None, 1) is None
    with pytest.raises(ValidationError):
        validate.equal('a', 'b')
    with pytest.raises(ValidationError):
        validate.equal(1, 2)
