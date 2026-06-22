import sqlite3; import os
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify, url_for, redirect, flash


from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash



app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

print("App iniciada")
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:4321", "http://127.0.0.1:4321"]}})



## Conectar a Base de datos
@app.route("/api/test")
def test():
    return jsonify({
        "message": "Backend funcionando"
    })

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_id_from_token():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    if not token.startswith("token-demo-"):
        return None

    try:
        return int(token.replace("token-demo-", ""))
    except ValueError:
        return None

@app.route("/api/register", methods=["POST"])
def api_register():
    username = request.form.get("nombre") or request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        return jsonify({"mensaje": "Faltan datos obligatorios."}), 400

    if len(username) < 3:
        return jsonify({"mensaje": "El nombre debe tener al menos 3 caracteres."}), 400

    if len(password) < 6:
        return jsonify({"mensaje": "La contraseña debe tener al menos 6 caracteres."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        conn.close()
        return jsonify({"mensaje": "El usuario o email ya está registrado."}), 409

    password_hash = generate_password_hash(password)

    cursor.execute("""
    INSERT INTO users 
    (username, email, password, tokens, intentos_fallidos, bloqueado, rol)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (username, email, password_hash, 2, 0, 0, "alumno"))

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Usuario registrado correctamente."}), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    email = data.get("email") if data else None
    password = data.get("password") if data else None

    if not email or not password:
        return jsonify({"mensaje": "Email y contraseña son obligatorios."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?",
        (email, email)
    )

    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"mensaje": "Email o contraseña incorrectos."}), 401

    # user[0] = id
    # user[1] = username
    # user[2] = email
    # user[3] = password
    # user[4] = tokens
    # user[5] = intentos_fallidos
    # user[6] = bloqueado
    # user[7] = rol

    if user[6] == 1:
        conn.close()
        return jsonify({
            "mensaje": "Cuenta bloqueada por demasiados intentos fallidos."
        }), 403

    password_hash = user[3]

    if not check_password_hash(password_hash, password):
        intentos_actuales = user[5] or 0
        nuevos_intentos = intentos_actuales + 1
        bloqueado = 1 if nuevos_intentos >= 3 else 0

        cursor.execute("""
            UPDATE users
            SET intentos_fallidos = ?, bloqueado = ?
            WHERE id = ?
        """, (nuevos_intentos, bloqueado, user[0]))

        conn.commit()
        conn.close()

        if bloqueado == 1:
            return jsonify({
                "mensaje": "Cuenta bloqueada tras 3 intentos fallidos."
            }), 403

        return jsonify({
            "mensaje": f"Email o contraseña incorrectos. Intentos: {nuevos_intentos}/3."
        }), 401

    cursor.execute("""
        UPDATE users
        SET intentos_fallidos = 0
        WHERE id = ?
    """, (user[0],))

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Login correcto.",
        "token": f"token-demo-{user[0]}",
        "usuario": {
            "id": user[0],
            "nombre": user[1],
            "email": user[2],
            "tokens": user[4],
            "rol": user[7]
        }
    }), 200

@app.route("/api/registro-profe", methods=["POST"])
def api_registro_profe():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    materia = request.form.get("materia")
    descripcion = request.form.get("descripcion")
    dias = request.form.getlist("dias")
    horarios = request.form.getlist("horarios")

    if not materia or not descripcion or not dias or not horarios:
        return jsonify({"mensaje": "Completá materia, descripción, días y horarios."}), 400

    if "certificado" not in request.files:
        return jsonify({"mensaje": "Adjuntá el certificado de materias aprobadas."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    cursor.execute("UPDATE users SET rol = ? WHERE id = ?", ("profe", user_id))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Postulación enviada correctamente."}), 200

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
    
    return "Dashboard"
    
@app.route("/logout")
def logout():

    if "user" not in session:
        return redirect(url_for("login"))
    
    username = session.get("user")

    session.pop("user", None)

    flash(f"Has cerrado la sesión de {username} correctamente", "success")

    return redirect(url_for("login"))

@app.route("/api/perfil", methods=["GET"])
def api_perfil():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, email, tokens, rol FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    return jsonify({
        "usuario": {
            "id": user[0],
            "nombre": user[1],
            "email": user[2],
            "tokens": user[3],
            "rol": user[4]
        },
        "reservas": []
    }), 200

## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True)
