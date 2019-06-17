from marshmallow.exceptions import ValidationError


class TestValidationError:
    def test_stores_message_in_list(self):
        err = ValidationError("foo")
        assert err.messages == ["foo"]

    def test_can_pass_list_of_messages(self):
        err = ValidationError(["foo", "bar"])
        assert err.messages == ["foo", "bar"]

    def test_stores_dictionaries(self):
        messages = {"user": {"email": ["email is invalid"]}}
        err = ValidationError(messages)
        assert err.messages == messages

    def test_can_store_field_name(self):
        err = ValidationError("invalid email", field_name="email")
        assert err.field_name == "email"

    def test_str(self):
        err = ValidationError("invalid email")
        assert str(err) == "invalid email"

        err2 = ValidationError("invalid email", "email")
        assert str(err2) == "invalid email"
