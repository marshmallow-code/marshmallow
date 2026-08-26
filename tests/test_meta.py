from marshmallow import Schema
from marshmallow.experimental.meta import meta


class Base(Schema):
    class Meta:
        foo = True


class TestMeta:
    def test_default_inheritance(self):
        @meta(bar=True)
        class Test(Base):
            pass

        assert getattr(Test.Meta, "foo", None)
        assert getattr(Test.Meta, "bar", None)

    def test_explicit_inheritance(self):
        class Parent(Schema):
            class Meta:
                bar = True

        @meta(Base.Meta, Parent.Meta, baz=True)
        class Test(Schema):
            pass

        assert getattr(Test.Meta, "foo", None)
        assert getattr(Test.Meta, "bar", None)
        assert getattr(Test.Meta, "baz", None)

    def test_clear_inheritance(self):
        @meta(Schema.Meta, bar=True)
        class Test(Base):
            pass

        assert not hasattr(Test.Meta, "foo")
