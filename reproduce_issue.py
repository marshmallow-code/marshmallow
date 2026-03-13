"""Reproduction script for marshmallow issue #2893."""
# ruff: noqa: T201, BLE001

from marshmallow import utils


def test_get_value_out_of_range_int():
    """Test get_value with out-of-range int index."""
    lst = [0, 1, 2, 3, 4, 5]
    try:
        val = utils.get_value(lst, 999, default=3)
        print(f"Case 1 (List out of range): {val}")
    except TypeError as e:
        print(f"Case 1 (List out of range) FAILED with TypeError: {e}")
    except Exception as e:
        print(f"Case 1 (List out of range) FAILED with {type(e).__name__}: {e}")

    dictionary = {1: "a", 2: "b", 3: "c"}
    try:
        val = utils.get_value(dictionary, 4, default="z")
        print(f"Case 2 (Dict missing int key): {val}")
    except TypeError as e:
        print(f"Case 2 (Dict missing int key) FAILED with TypeError: {e}")
    except Exception as e:
        print(f"Case 2 (Dict missing int key) FAILED with {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_get_value_out_of_range_int()
