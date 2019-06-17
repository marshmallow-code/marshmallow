import datetime as dt
from functools import wraps

from flask import Flask, request, g, jsonify
import peewee as pw
from marshmallow import (
    Schema,
    fields,
    validate,
    pre_load,
    post_dump,
    post_load,
    ValidationError,
)

app = Flask(__name__)
db = pw.SqliteDatabase("/tmp/todo.db")

###### MODELS #####


class BaseModel(pw.Model):
    """Base model class. All descendants share the same database."""

    class Meta:
        database = db


class User(BaseModel):
    email = pw.CharField(max_length=80, unique=True)
    password = pw.CharField()
    joined_on = pw.DateTimeField()


class Todo(BaseModel):
    content = pw.TextField()
    is_done = pw.BooleanField(default=False)
    user = pw.ForeignKeyField(User)
    posted_on = pw.DateTimeField()

    class Meta:
        order_by = ("-posted_on",)


def create_tables():
    db.connect()
    User.create_table(True)
    Todo.create_table(True)


##### SCHEMAS #####


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    email = fields.Str(
        required=True, validate=validate.Email(error="Not a valid email address")
    )
    password = fields.Str(
        required=True, validate=[validate.Length(min=6, max=36)], load_only=True
    )
    joined_on = fields.DateTime(dump_only=True)

    # Clean up data
    @pre_load
    def process_input(self, data, **kwargs):
        data["email"] = data["email"].lower().strip()
        return data

    # We add a post_dump hook to add an envelope to responses
    @post_dump(pass_many=True)
    def wrap(self, data, many, **kwargs):
        key = "users" if many else "user"
        return {key: data}


class TodoSchema(Schema):
    id = fields.Int(dump_only=True)
    done = fields.Boolean(attribute="is_done", missing=False)
    user = fields.Nested(UserSchema, exclude=("joined_on", "password"), dump_only=True)
    content = fields.Str(required=True)
    posted_on = fields.DateTime(dump_only=True)

    # Again, add an envelope to responses
    @post_dump(pass_many=True)
    def wrap(self, data, many, **kwargs):
        key = "todos" if many else "todo"
        return {key: data}

    # We use make_object to create a new Todo from validated data
    @post_load
    def make_object(self, data, **kwargs):
        if not data:
            return None
        return Todo(
            content=data["content"],
            is_done=data["is_done"],
            posted_on=dt.datetime.utcnow(),
        )


user_schema = UserSchema()
todo_schema = TodoSchema()
todos_schema = TodoSchema(many=True)

###### HELPERS ######


def check_auth(email, password):
    """Check if a username/password combination is valid.
    """
    try:
        user = User.get(User.email == email)
    except User.DoesNotExist:
        return False
    return password == user.password


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            resp = jsonify({"message": "Please authenticate."})
            resp.status_code = 401
            resp.headers["WWW-Authenticate"] = 'Basic realm="Example"'
            return resp
        kwargs["user"] = User.get(User.email == auth.username)
        return f(*args, **kwargs)

    return decorated


# Ensure a separate connection for each thread
@app.before_request
def before_request():
    g.db = db
    g.db.connect()


@app.after_request
def after_request(response):
    g.db.close()
    return response


#### API #####


@app.route("/register", methods=["POST"])
def register():
    json_input = request.get_json()
    try:
        data = user_schema.load(json_input)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422
    try:  # Use get to see if user already exists
        User.get(User.email == data["email"])
    except User.DoesNotExist:
        user = User.create(
            email=data["email"], joined_on=dt.datetime.now(), password=data["password"]
        )
        message = "Successfully created user: {}".format(user.email)
    else:
        return jsonify({"errors": "That email address is already in the database"}), 400

    data = user_schema.dump(user)
    data["message"] = message
    return jsonify(data), 201


@app.route("/todos/", methods=["GET"])
def get_todos():
    todos = Todo.select().order_by(Todo.posted_on.asc())  # Get all todos
    result = todos_schema.dump(list(todos))
    return jsonify(result)


@app.route("/todos/<int:pk>")
def get_todo(pk):
    todo = Todo.get(Todo.id == pk)
    if not todo:
        return jsonify({"errors": "Todo could not be find"}), 404
    result = todo_schema.dump(todo)
    return jsonify(result)


@app.route("/todos/<int:pk>/toggle", methods=["POST", "PUT"])
def toggledone(pk):
    try:
        todo = Todo.get(Todo.id == pk)
    except Todo.DoesNotExist:
        return jsonify({"message": "Todo could not be found"}), 404
    status = not todo.is_done
    update_query = todo.update(is_done=status)
    update_query.execute()
    result = todo_schema.dump(todo)
    return jsonify(result)


@app.route("/todos/", methods=["POST"])
@requires_auth
def new_todo(user):
    json_input = request.get_json()
    try:
        todo = todo_schema.load(json_input)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422
    todo.user = user
    todo.save()
    result = todo_schema.dump(todo)
    return jsonify(result)


if __name__ == "__main__":
    create_tables()
    app.run(port=5000, debug=True)
