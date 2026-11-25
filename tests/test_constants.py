import copy
import pickle

from marshmallow.constants import _Missing, missing


def test_missing_singleton_copy():
    assert copy.copy(missing) is missing
    assert copy.deepcopy(missing) is missing
    assert pickle.loads(pickle.dumps(missing)) is missing


def test_missing_singleton_recreate():
    assert _Missing() is missing
