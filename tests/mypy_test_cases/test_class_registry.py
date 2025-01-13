from marshmallow import class_registry

# Works without passing `all`
class_registry.get_class("MySchema")
