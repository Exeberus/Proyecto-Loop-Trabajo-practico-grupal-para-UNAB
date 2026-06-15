from flask import Flask

from backend.extensions import db

from backend.models.user import User
from backend.models.conversation import Conversation
from backend.models.message import Message

from backend.routes.chat_routes import chat_bp


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///loop.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)

print("Loop Backend iniciado correctamente")

app.register_blueprint(chat_bp)


with app.app_context():
    db.create_all()

@app.route("/create-test-users")
def create_test_users():

    from backend.models.user import User

    if User.query.count() > 0:
        return {
            "message": "Usuarios ya existentes"
        }

    user1 = User(
        username="Rodrigo"
    )

    user2 = User(
        username="Tutor"
    )

    db.session.add(user1)
    db.session.add(user2)

    db.session.commit()

    return {
        "message": "Usuarios creados"
    }

@app.route("/users")
def list_users():

    from backend.models.user import User

    users = User.query.all()

    response = []

    for user in users:
        response.append({
            "id": user.id,
            "username": user.username
        })

    return response

if __name__ == "__main__":
    app.run(
        debug=True
    )