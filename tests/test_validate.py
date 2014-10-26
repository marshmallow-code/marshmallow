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
