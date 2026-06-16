import sqlite3; import os
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify, url_for, redirect, flash
from routes.chat_routes import chat_bp

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

print("App iniciada")
CORS(app)

app.register_blueprint(chat_bp)

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

@app.route('/', methods=["GET", "POST"])
def main_page():
    
    is_logued = None

    if "user" in session:
        is_logued = True

    return render_template("main_page.html", is_logued=is_logued)

@app.route('/register', methods=["GET", "POST"])
def register():

    errors = []
    special_chars = "!@#$%^&*()-_=+[]{};:,.<>?/\\|" ## Caracteres especiales
    
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if len(username) < 3:
            errors.append("El usuario debe tener al menos 3 caracteres ")
    
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres ")
        
        if not any (char in special_chars for char in password): 
            errors.append("La contraseña debe tener al menos uno de estos carácteres especiales: !@#$%^&*()-_=+[]{};:,.<>?/\\| ")
        
        if not any(char.isdigit() for char in password):
            errors.append("La contraseña debe tener al menos un número")

        if password_confirm != password:
            errors.append("Las contraseñas no coinciden")

        if " " in username:
            errors.append("El usuario no puede tener espacios ")

        if "@" not in email:
            errors.append("Email inválido ")
        
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )

        if cursor.fetchone():
            errors.append("Este nombre de Usuario ya está registrado")

        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        )
            
        if cursor.fetchone():
            errors.append("Este Email ya está registrado")

        if not errors:

            password_hash = generate_password_hash(password)

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )

            conn.commit()

            flash("Cuenta creada correctamente. Porfavor inicie sesión.", "success")

            conn.close()
            
            return redirect(url_for("login"))
        
        conn.close()

    return render_template("register.html", errors=errors)

@app.route('/login', methods=["GET", "POST"])
def login():
    
    error = None

    if request.method == "POST":

        login_input = request.form["login"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username = ? OR email = ?
            """,
            (login_input, login_input)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session["user"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            error = "Usuario, Email o contraseña incorrectos"
        
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        flash("Debes iniciar sesión para acceder al dashboard.", "error")

        return redirect(url_for("login"))
    
    user_id = session["user"]

    rating = get_user_rating(user_id)
    
    return render_template("dashboard.html", rating=rating)
    
@app.route("/logout")
def logout():

    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session.get("user")

    session.pop("user", None)

    flash(f"Has cerrado la sesión de {username} correctamente", "success")

    return redirect(url_for("login"))

@app.route("/rate", methods=["POST"])
def rate():

    if "user" not in session:
        return jsonify({"error": "No logueado"}), 401

    data = request.json

    user_id = data["user_id"]
    stars = data["stars"]

    rater_id = session["user"]

    if stars < 1 or stars > 5:
        return jsonify({"error": "Invalid stars"}), 400

    add_rating(user_id, rater_id, stars)

    return jsonify({"message": "Rating enviado"})

def add_rating(user_id, rater_id, stars):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ratings (user_id, rater_id, stars)
        VALUES (?, ?, ?)
    """, (user_id, rater_id, stars))

    conn.commit()
    conn.close()

def get_user_rating(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT AVG(stars)
        FROM ratings
        WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()[0]

    conn.close()

    return round(result, 1) if result else 0

@app.route("/profile/<int:user_id>")
def profile(user_id):

    username, rating = get_user_rating_with_name(user_id)

    return render_template(
        "profiles.html",
        username=username,
        rating=rating
    )

@app.route("/test-chat")
def test_chat():

    from services.chat_service import create_conversation

    conversation = create_conversation(1, 2)

    return conversation

@app.route("/test-message")
def test_message():

    from services.chat_service import send_message

    message = send_message(
        1,              # conversation_id
        1,              # sender_id
        "Hola mundo"
    )

    return message

@app.route("/test-get-messages")
def test_get_messages():

    from services.chat_service import get_messages

    return get_messages(1)

def get_user_rating_with_name(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.username, AVG(r.stars)
        FROM users u
        LEFT JOIN ratings r ON u.id = r.user_id
        WHERE u.id = ?
        GROUP BY u.id
    """, (user_id,))

    result = cursor.fetchone()

    conn.close()

    if result:
        username = result[0]
        rating = round(result[1], 1) if result[1] else 0
        return username, rating

    return None, 0

## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True)