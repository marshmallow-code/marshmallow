# -*- coding: utf-8 -*-

from marshmallow.exceptions import ValidationError

class TestValidationError:

    def test_stores_message_in_list(self):
        err = ValidationError('foo')
        assert err.messages == ['foo']

    def test_can_pass_list_of_messages(self):
        err = ValidationError(['foo', 'bar'])
        assert err.messages == ['foo', 'bar']
