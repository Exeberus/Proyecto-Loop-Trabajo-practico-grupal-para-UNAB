import sqlite3; import os
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

print("App iniciada")
CORS(app)

## Conectar a Base de datos
@app.route("/api/test")
def test():
    return jsonify({
        "message": "Backend funcionando"
    })

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    print("BD ABIERTA:", DB_PATH)
    return sqlite3.connect(DB_PATH)

@app.route('/register', methods=["GET", "POST"])
def register():

    errors = []
    
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if len(username) < 3:
            errors.append("El usuario debe tener al menos 3 caracteres ")
    
        if len (password) < 6:
            errors.append("La contraseña debe tener al menos 6 caracteres ")

        if " " in username:
            errors.append("El usuario no puede tener espacios ")

        if "@" not in email:
            errors.append("Email inválido ")

        if len(errors) == 0:

            conn = get_db()
            cursor = conn.cursor()

            print("CARPETA ACTUAL FLASK:", os.getcwd())
            print("EXISTE DB:", os.path.exists("database.db"))

            cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            """)

            print("TABLAS EN REGISTER:", cursor.fetchall())

            cursor.execute("SELECT * FROM users")
            print("SELECT USERS FUNCIONA")

            conn = get_db()
            cursor = conn.cursor()

            password_hash = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )

            conn.commit()
            conn.close()

    return render_template("register.html", errors=errors)

@app.route('/login', methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        print("ENTRÓ AL POST")
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session["user"] = username
            return "Login correcto"
        else:
            return "Usuario o contraseña incorrectos"
        
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user" in session:
        return f"Bienvenido {session['user']}"
    else:
        return "No estás logueado"
    
@app.route("/logout")
def logout():

    session.pop("user", None)

    return "Sesión cerrada"

## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True)