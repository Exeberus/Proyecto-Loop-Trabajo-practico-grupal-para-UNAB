import sqlite3
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify

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

def get_db():
    conn = sqlite3.connect("database.db")
    return conn

@app.route('/register', methods=["GET", "POST"])
def register():

    error = None
    
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 3:
            error = "El usuario debe tener al menos 3 caracteres"
    
        elif len (password) < 6:
            error = "La contraseña debe tener al menos 6 caracteres"

        elif " " in username:
            error = "El usuario no puede tener espacios"

        else:

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            conn.close()

            return "Usuario registrado correctamente"

    return render_template("register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        print("ENTRÓ AL POST")
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        if user:
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