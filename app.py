import sqlite3
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

## Conectar a Base de datos
def get_db():
    conn = sqlite3.connect("database.db")
    return conn

@app.route('/register', methods=["GET", "POST"])
def register():
    
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()
        return "Usuario registrado"

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

    if "user" in session:
        session.pop("user", None)
        return "Sesión cerrada"


## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True)