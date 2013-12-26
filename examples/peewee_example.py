import datetime as dt
from functools import wraps

from flask import Flask, request, g, jsonify
import peewee as pw
from marshmallow import Serializer, fields

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

##### SERIALIZERS #####

class UserSerializer(Serializer):
    class Meta:
        fields = ('email', 'joined_on')

class TodoSerializer(Serializer):
    done = fields.Boolean(attribute='is_done')
    user = fields.Nested(UserSerializer)
    class Meta:
        additional = ('id', 'content', 'posted_on')

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
    try:  # Use get to see if user already to exists
        User.get(User.email == request.json['email'])
        message = "That email address is already in the database."
    except User.DoesNotExist:
        user = User.create(email=request.json['email'], joined_on=dt.datetime.now(),
                            password=request.json['password'])
        message = "Successfully created user: {0}".format(user.email)
    return jsonify({'message': message, "user": UserSerializer(user).data})

@app.route("/api/v1/todos")
def get_todos():
    todos = Todo.select()  # Get all todos
    serialized = TodoSerializer(list(todos), many=True)
    return jsonify({"todos": serialized.data})

@app.route("/api/v1/todos/<int:pk>")
def get_todo(pk):
    try:
        todo = Todo.get(Todo.id == pk)
    except Todo.DoesNotExist:
        return jsonify({"message": "Todo could not be found"})
    return jsonify({"todo": TodoSerializer(todo).data})

@app.route("/api/v1/todos/<int:pk>/toggle", methods=["POST"])
def toggledone(pk):
    try:
        todo = Todo.get(Todo.id == pk)
    except Todo.DoesNotExist:
        return jsonify({"message": "Todo could not be found"})
    status = not todo.is_done
    update_query = todo.update(is_done=status)
    update_query.execute()
    return jsonify({"message": "Successfully toggled status.",
                    "todo": TodoSerializer(todo).data})

@app.route("/api/v1/todos/new", methods=["POST"])
@requires_auth
def new_todo():
    user = User.get(User.email == request.authorization.username)
    todo_content = request.json['content']
    todo = Todo.create(content=todo_content, user=user, posted_on=dt.datetime.now())
    return jsonify({"message": "Successfully created new todo item.",
                    "todo": TodoSerializer(todo).data})

if __name__ == '__main__':
    create_tables()
    app.run(port=5000, debug=True)
