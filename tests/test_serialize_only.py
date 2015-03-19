import pytest
from tests.base import BlogSchema

def create_keys(only):
        d = {}
        for vals in only:
            l = d
            for k in vals.split("."):
                if not k in l: l[k] = {}  #if the key isn't there yet add it to d
                l = l[k]
        return d


def validate_fields(only_dict, result):
    assert only_dict.keys() == result.keys()
    for k, v in only_dict.iteritems():
        if v and not isinstance(result[k], list):
            validate_fields(v, result[k])


def test_serialize_with_only(blog):
    blog_schema = BlogSchema()
    only = ("title", "user")

    res, _ = blog_schema.dump(blog)
    assert set(only) != set(res.keys())

    res, _ = blog_schema.dump(blog, only=only)
    assert set(only) == set(res.keys())

    only = ("title", "user.name")
    res, _ = blog_schema.dump(blog, only=only)
    only_dict = create_keys(only)
    validate_fields(only_dict, res)


def test_serialize_with_only2(blog):
    blog_schema = BlogSchema()
    only = ("title", "user", "collaborators")

    res, _ = blog_schema.dump(blog)
    assert set(only) != set(res.keys())

    res, _ = blog_schema.dump(blog, only=only)
    assert set(only) == set(res.keys())

    only = ("title", "user.name", "collaborators.name")
    res, _ = blog_schema.dump(blog, only=only)

    print res
    only_dict = create_keys(only)
    validate_fields(only_dict, res)