from flask import Flask
from routes.users import users_bp

app = Flask(__name__)

app.register_blueprint(users_bp)

@app.route("/api/test")
def test():
    return {"message": "Backend funcionando"}

if __name__ == "__main__":
    app.run(debug=True)