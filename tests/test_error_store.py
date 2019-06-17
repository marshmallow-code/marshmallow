from collections import namedtuple

from marshmallow import missing
from marshmallow.error_store import merge_errors


def test_missing_is_falsy():
    assert bool(missing) is False


CustomError = namedtuple("CustomError", ["code", "message"])


class TestMergeErrors:
    def test_merging_none_and_string(self):
        assert "error1" == merge_errors(None, "error1")

    def test_merging_none_and_custom_error(self):
        assert CustomError(123, "error1") == merge_errors(
            None, CustomError(123, "error1")
        )

    def test_merging_none_and_list(self):
        assert ["error1", "error2"] == merge_errors(None, ["error1", "error2"])

    def test_merging_none_and_dict(self):
        assert {"field1": "error1"} == merge_errors(None, {"field1": "error1"})

    def test_merging_string_and_none(self):
        assert "error1" == merge_errors("error1", None)

    def test_merging_custom_error_and_none(self):
        assert CustomError(123, "error1") == merge_errors(
            CustomError(123, "error1"), None
        )

    def test_merging_list_and_none(self):
        assert ["error1", "error2"] == merge_errors(["error1", "error2"], None)

    def test_merging_dict_and_none(self):
        assert {"field1": "error1"} == merge_errors({"field1": "error1"}, None)

    def test_merging_string_and_string(self):
        assert ["error1", "error2"] == merge_errors("error1", "error2")

    def test_merging_custom_error_and_string(self):
        assert [CustomError(123, "error1"), "error2"] == merge_errors(
            CustomError(123, "error1"), "error2"
        )

    def test_merging_string_and_custom_error(self):
        assert ["error1", CustomError(123, "error2")] == merge_errors(
            "error1", CustomError(123, "error2")
        )

    def test_merging_custom_error_and_custom_error(self):
        assert [CustomError(123, "error1"), CustomError(456, "error2")] == merge_errors(
            CustomError(123, "error1"), CustomError(456, "error2")
        )

    def test_merging_string_and_list(self):
        assert ["error1", "error2"] == merge_errors("error1", ["error2"])

    def test_merging_string_and_dict(self):
        assert {"_schema": "error1", "field1": "error2"} == merge_errors(
            "error1", {"field1": "error2"}
        )

    def test_merging_string_and_dict_with_schema_error(self):
        assert {"_schema": ["error1", "error2"], "field1": "error3"} == merge_errors(
            "error1", {"_schema": "error2", "field1": "error3"}
        )

    def test_merging_custom_error_and_list(self):
        assert [CustomError(123, "error1"), "error2"] == merge_errors(
            CustomError(123, "error1"), ["error2"]
        )

    def test_merging_custom_error_and_dict(self):
        assert {
            "_schema": CustomError(123, "error1"),
            "field1": "error2",
        } == merge_errors(CustomError(123, "error1"), {"field1": "error2"})

    def test_merging_custom_error_and_dict_with_schema_error(self):
        assert {
            "_schema": [CustomError(123, "error1"), "error2"],
            "field1": "error3",
        } == merge_errors(
            CustomError(123, "error1"), {"_schema": "error2", "field1": "error3"}
        )

    def test_merging_list_and_string(self):
        assert ["error1", "error2"] == merge_errors(["error1"], "error2")

    def test_merging_list_and_custom_error(self):
        assert ["error1", CustomError(123, "error2")] == merge_errors(
            ["error1"], CustomError(123, "error2")
        )

    def test_merging_list_and_list(self):
        assert ["error1", "error2"] == merge_errors(["error1"], ["error2"])

    def test_merging_list_and_dict(self):
        assert {"_schema": ["error1"], "field1": "error2"} == merge_errors(
            ["error1"], {"field1": "error2"}
        )

    def test_merging_list_and_dict_with_schema_error(self):
        assert {"_schema": ["error1", "error2"], "field1": "error3"} == merge_errors(
            ["error1"], {"_schema": "error2", "field1": "error3"}
        )

    def test_merging_dict_and_string(self):
        assert {"_schema": "error2", "field1": "error1"} == merge_errors(
            {"field1": "error1"}, "error2"
        )

    def test_merging_dict_and_custom_error(self):
        assert {
            "_schema": CustomError(123, "error2"),
            "field1": "error1",
        } == merge_errors({"field1": "error1"}, CustomError(123, "error2"))

    def test_merging_dict_and_list(self):
        assert {"_schema": ["error2"], "field1": "error1"} == merge_errors(
            {"field1": "error1"}, ["error2"]
        )

    def test_merging_dict_and_dict(self):
        assert {
            "field1": "error1",
            "field2": ["error2", "error3"],
            "field3": "error4",
        } == merge_errors(
            {"field1": "error1", "field2": "error2"},
            {"field2": "error3", "field3": "error4"},
        )

    def test_deep_merging_dicts(self):
        assert {"field1": {"field2": ["error1", "error2"]}} == merge_errors(
            {"field1": {"field2": "error1"}}, {"field1": {"field2": "error2"}}
        )
