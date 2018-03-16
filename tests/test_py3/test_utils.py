from marshmallow import fields, Schema


# Regression test for https://github.com/marshmallow-code/marshmallow/issues/540
def test_function_field_using_type_annotation():
    def get_split_words(value: str):
        return value.split(';')

    class MySchema(Schema):
        friends = fields.Function(deserialize=get_split_words)

    data = {'name': 'Bruce Wayne', 'friends': 'Clark;Alfred;Robin'}
    result = MySchema().load(data)
    assert result == {'friends': ['Clark', 'Alfred', 'Robin']}
