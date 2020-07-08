from marshmallow import orderedset


def test_intersection():
    s = orderedset.OrderedSet([2, 1, 3])
    t = orderedset.OrderedSet([3, 2])

    assert s.intersection(t) == {2, 3}


def test_union():
    s = orderedset.OrderedSet([2, 1, 3])
    t = orderedset.OrderedSet([3, 2])

    assert s.union(t) == {1, 2, 3}


def test_difference():
    s = orderedset.OrderedSet([2, 1, 3])
    t = orderedset.OrderedSet([3, 2])

    assert s.difference(t) == {1}
