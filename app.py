## Imports de funciones:
from services.auth_service import validate_register
from services.rating import add_rating, get_user_rating_with_name, get_user_rating

import sqlite3; import os

from get_db import get_db
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify, url_for, redirect, flash
from routes.chat_routes import chat_bp

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

print("App iniciada")
CORS(app)

conn = get_db()

app.register_blueprint(chat_bp)

## Conectar a Base de datos
@app.route("/api/test")
def test():
    return jsonify({
        "message": "Backend funcionando"
    })

@app.route('/', methods=["GET", "POST"])
def main_page():
    
    is_logued = None

    if "user" in session:
        is_logued = True

    return render_template("main_page.html", is_logued=is_logued)

@app.route('/register', methods=["GET", "POST"])
def register():

    errors = []

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        errors = validate_register(
            username,
            email,
            password,
            password_confirm
        )

        if not errors:

            conn = get_db()
            cursor = conn.cursor()

            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users
                (username, email, password)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash)
            )

            conn.commit()
            conn.close()

            flash(
                "Cuenta creada correctamente. Porfavor inicie sesión.",
                "success"
            )

            return redirect(url_for("login"))

    return render_template(
        "register.html",
        errors=errors
    )

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

            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("dashboard"))
        
        else:

            error = "Usuario, Email o contraseña incorrectos"
        
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():

    if "user" not in session:

        flash("Debes iniciar sesión para acceder al dashboard.", "error")

        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    rating = get_user_rating(user_id)
    
    return render_template("dashboard.html", rating=rating)
    
@app.route("/logout")
def logout():

    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session.get("username")

    session.pop("user_id", None)
    session.pop("username", None)

    flash(f"Has cerrado la sesión de {username} correctamente", "success")

    return redirect(url_for("login"))

@app.route("/rate", methods=["POST"])
def rate():

    if "user" not in session:
        return jsonify({"error": "No logueado"}), 401

    data = request.json

    user_id = data["user_id"]
    stars = data["stars"]

    rater_id = session["user_id"]

    if stars < 1 or stars > 5:
        return jsonify({"error": "Invalid stars"}), 400

    add_rating(user_id, rater_id, stars)

    return jsonify({"message": "Rating enviado"})

@app.route("/profile/<int:user_id>")
def profile(user_id):

    username, rating = get_user_rating_with_name(user_id)

    return render_template(
        "profiles.html",
        username=username,
        rating=rating
    )

## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True)