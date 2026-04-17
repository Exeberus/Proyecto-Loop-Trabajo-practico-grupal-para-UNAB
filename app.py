from flask import Flask
from routes.users import users_bp

app = Flask(__name__)

app.register_blueprint(users_bp)

@app.route("/api/users")
def test():
    return {"message": "Hola desde Flask!"}

if __name__ == "__main__":
    app.run(debug=True)