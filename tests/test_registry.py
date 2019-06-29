import pytest

from marshmallow import Schema, fields, class_registry
from marshmallow.exceptions import RegistryError


def test_serializer_has_class_registry():
    class MySchema(Schema):
        pass

    class MySubSchema(Schema):
        pass

    assert "MySchema" in class_registry._registry
    assert "MySubSchema" in class_registry._registry

    #  by fullpath
    assert "tests.test_registry.MySchema" in class_registry._registry
    assert "tests.test_registry.MySubSchema" in class_registry._registry


def test_register_class_meta_option():
    class UnregisteredSchema(Schema):
        class Meta:
            register = False

    class RegisteredSchema(Schema):
        class Meta:
            register = True

    class RegisteredOverrideSchema(UnregisteredSchema):
        class Meta:
            register = True

    class UnregisteredOverrideSchema(RegisteredSchema):
        class Meta:
            register = False

    assert "UnregisteredSchema" not in class_registry._registry
    assert "tests.test_registry.UnregisteredSchema" not in class_registry._registry

    assert "RegisteredSchema" in class_registry._registry
    assert "tests.test_registry.RegisteredSchema" in class_registry._registry

    assert "RegisteredOverrideSchema" in class_registry._registry
    assert "tests.test_registry.RegisteredOverrideSchema" in class_registry._registry

    assert "UnregisteredOverrideSchema" not in class_registry._registry
    assert (
        "tests.test_registry.UnregisteredOverrideSchema" not in class_registry._registry
    )


def test_serializer_class_registry_register_same_classname_different_module():

    reglen = len(class_registry._registry)

    type("MyTestRegSchema", (Schema,), {"__module__": "modA"})

    assert "MyTestRegSchema" in class_registry._registry
    assert len(class_registry._registry.get("MyTestRegSchema")) == 1
    assert "modA.MyTestRegSchema" in class_registry._registry
    #  storing for classname and fullpath
    assert len(class_registry._registry) == reglen + 2

    type("MyTestRegSchema", (Schema,), {"__module__": "modB"})

    assert "MyTestRegSchema" in class_registry._registry
    #  aggregating classes with same name from different modules
    assert len(class_registry._registry.get("MyTestRegSchema")) == 2
    assert "modB.MyTestRegSchema" in class_registry._registry
    #  storing for same classname (+0) and different module (+1)
    assert len(class_registry._registry) == reglen + 2 + 1

    type("MyTestRegSchema", (Schema,), {"__module__": "modB"})

    assert "MyTestRegSchema" in class_registry._registry
    #  only the class with matching module has been replaced
    assert len(class_registry._registry.get("MyTestRegSchema")) == 2
    assert "modB.MyTestRegSchema" in class_registry._registry
    #  only the class with matching module has been replaced (+0)
    assert len(class_registry._registry) == reglen + 2 + 1


def test_serializer_class_registry_override_if_same_classname_same_module():

    reglen = len(class_registry._registry)

    type("MyTestReg2Schema", (Schema,), {"__module__": "SameModulePath"})

    assert "MyTestReg2Schema" in class_registry._registry
    assert len(class_registry._registry.get("MyTestReg2Schema")) == 1
    assert "SameModulePath.MyTestReg2Schema" in class_registry._registry
    assert len(class_registry._registry.get("SameModulePath.MyTestReg2Schema")) == 1
    #  storing for classname and fullpath
    assert len(class_registry._registry) == reglen + 2

    type("MyTestReg2Schema", (Schema,), {"__module__": "SameModulePath"})

    assert "MyTestReg2Schema" in class_registry._registry
    #  overriding same class name and same module
    assert len(class_registry._registry.get("MyTestReg2Schema")) == 1
    assert "SameModulePath.MyTestReg2Schema" in class_registry._registry
    #  overriding same fullpath
    assert len(class_registry._registry.get("SameModulePath.MyTestReg2Schema")) == 1
    #  overriding for same classname (+0) and different module (+0)
    assert len(class_registry._registry) == reglen + 2


class A:
    def __init__(self, _id, b=None):
        self.id = _id
        self.b = b


class B:
    def __init__(self, _id, a=None):
        self.id = _id
        self.a = a


class C:
    def __init__(self, _id, bs=None):
        self.id = _id
        self.bs = bs or []


class ASchema(Schema):
    id = fields.Integer()
    b = fields.Nested("BSchema", exclude=("a",))


class BSchema(Schema):
    id = fields.Integer()
    a = fields.Nested("ASchema")


class CSchema(Schema):
    id = fields.Integer()
    bs = fields.Nested("BSchema", many=True)


def test_two_way_nesting():
    a_obj = A(1)
    b_obj = B(2, a=a_obj)
    a_obj.b = b_obj

    a_serialized = ASchema().dump(a_obj)
    b_serialized = BSchema().dump(b_obj)
    assert a_serialized["b"]["id"] == b_obj.id
    assert b_serialized["a"]["id"] == a_obj.id


def test_nesting_with_class_name_many():
    c_obj = C(1, bs=[B(2), B(3), B(4)])

    c_serialized = CSchema().dump(c_obj)

    assert len(c_serialized["bs"]) == len(c_obj.bs)
    assert c_serialized["bs"][0]["id"] == c_obj.bs[0].id


def test_invalid_class_name_in_nested_field_raises_error(user):
    class MySchema(Schema):
        nf = fields.Nested("notfound")

    sch = MySchema()
    msg = "Class with name {!r} was not found".format("notfound")
    with pytest.raises(RegistryError, match=msg):
        sch.dump({"nf": None})


class FooSerializer(Schema):
    _id = fields.Integer()


def test_multiple_classes_with_same_name_raises_error():
    # Import a class with the same name
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    class MySchema(Schema):
        foo = fields.Nested("FooSerializer")

    # Using a nested field with the class name fails because there are
    # two defined classes with the same name
    sch = MySchema()
    msg = "Multiple classes with name {!r} were found.".format("FooSerializer")
    with pytest.raises(RegistryError, match=msg):
        sch.dump({"foo": {"_id": 1}})


def test_multiple_classes_with_all():
    # Import a class with the same name
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    classes = class_registry.get_class("FooSerializer", all=True)
    assert len(classes) == 2


def test_can_use_full_module_path_to_class():
    from .foo_serializer import FooSerializer as FooSerializer1  # noqa

    # Using full paths is ok

    class Schema1(Schema):
        foo = fields.Nested("tests.foo_serializer.FooSerializer")

    sch = Schema1()

    # Note: The arguments here don't matter. What matters is that no
    # error is raised
    assert sch.dump({"foo": {"_id": 42}})

    class Schema2(Schema):
        foo = fields.Nested("tests.test_registry.FooSerializer")

    sch = Schema2()
    assert sch.dump({"foo": {"_id": 42}})
