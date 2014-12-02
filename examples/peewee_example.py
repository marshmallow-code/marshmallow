import datetime as dt
from functools import wraps

from flask import Flask, request, g, jsonify
import peewee as pw
from marshmallow import Schema, fields, ValidationError

app = Flask(__name__)
db = pw.SqliteDatabase("/tmp/todo.db")

###### MODELS #####

class BaseModel(pw.Model):
    """Base model class. All descendants share the same database."""
    def __marshallable__(self):
        """Return the marshallable dictionary that will be serialized by
        marshmallow. Peewee models have a dictionary representation where the
        ``_data`` key contains all the field:value pairs for the object.
        """
        return dict(self.__dict__)['_data']

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
        order_by = ('-posted_on', )

def create_tables():
    db.connect()
    User.create_table(True)
    Todo.create_table(True)

##### SCHEMAS #####

class UserSchema(Schema):
    class Meta:
        fields = ('id', 'email', 'joined_on')

class TodoSchema(Schema):
    done = fields.Boolean(attribute='is_done')
    user = fields.Nested(UserSchema, exclude=('joined_on',))
    content = fields.Str(required=True)
    posted_on = fields.DateTime()

    class Meta:
        additional = ('id', )

    def make_object(self, data):
        if data.get('id'):
            todo = Todo.get(Todo.id == data['id'])
        else:
            user_data = data.get('user')
            if not user_data:
                raise ValidationError('Must provide user when creating a new todo item.')
            user = User.get(User.email == user_data['email'])
            todo = Todo(content=data['content'],
                        user=user,
                        posted_on=dt.datetime.utcnow())
        return todo

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
            resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'
            return resp
        return f(*args, **kwargs)
    return decorated

#### API #####

# Ensure a separate connection for each thread
@app.before_request
def before_request():
    g.db = db
    g.db.connect()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route("/api/v1/register", methods=["POST"])
def register():
    json_input = request.get_json()
    if not json_input:
        return jsonify({'message': 'Must provide username and password'}), 400
    try:  # Use get to see if user already to exists
        User.get(User.email == request.json['email'])
        message = "That email address is already in the database."
    except User.DoesNotExist:
        user = User.create(email=json_input['email'], joined_on=dt.datetime.now(),
                            password=json_input['password'])
        message = "Successfully created user: {0}".format(user.email)
    data, errors = user_schema.dump(user)
    if errors:
        return jsonify(errors), 400
    return jsonify({'message': message, "user": data})

@app.route("/api/v1/todos/", methods=['GET'])
def get_todos():
    todos = Todo.select()  # Get all todos
    data, errors = todos_schema.dump(list(todos))
    if errors:
        return jsonify(errors), 400
    return jsonify({"todos": data})

@app.route("/api/v1/todos/<int:pk>")
def get_todo(pk):
    try:
        todo, errs = todo_schema.load({'id': pk})
    except Todo.DoesNotExist:
        return jsonify({"message": "Todo could not be found"})
    data, errors = todo_schema.dump(todo)
    if errors:
        return jsonify(errors), 400
    return jsonify({"todo": data})

@app.route("/api/v1/todos/<int:pk>/toggle", methods=["POST", "PUT"])
def toggledone(pk):
    try:
        todo = Todo.get(Todo.id == pk)
    except Todo.DoesNotExist:
        return jsonify({"message": "Todo could not be found"})
    status = not todo.is_done
    update_query = todo.update(is_done=status)
    update_query.execute()
    data, errors = todo_schema.dump(todo)
    if errors:
        return jsonify(errors), 400
    return jsonify({"message": "Successfully toggled status.",
                    "todo": data})

@app.route("/api/v1/todos/", methods=["POST"])
@requires_auth
def new_todo():
    json_input = request.get_json()
    if not json_input:
        return jsonify({'message': 'No input provided'}), 400
    # Deserialize to a new Todo
    todo, errors = todo_schema.load({
        'content': json_input.get('content'),
        'user': {'email': request.authorization.username}
    })
    if errors:
        return jsonify(errors), 400
    todo.save()
    result = todo_schema.dump(todo)
    return jsonify({"message": "Successfully created new todo item.",
                    "todo": result.data})

if __name__ == '__main__':
    create_tables()
    app.run(port=5000, debug=True)
