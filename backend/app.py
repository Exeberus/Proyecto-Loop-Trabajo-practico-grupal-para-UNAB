import json
import secrets
import sqlite3; import os
import threading
from datetime import datetime, timedelta
from flask_cors import CORS
from flask import Flask, render_template, request, session, jsonify, url_for, redirect, flash
from werkzeug.utils import secure_filename


from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash



app = Flask(__name__)
app.secret_key = '0f2e4c18ca9ae37290cad43b86fad8f65aad8cf682561b0b3a0650c80737df45'

print("App iniciada")
ALLOWED_ORIGINS = [
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "https://loop-dwt.pages.dev",
]
CORS(
    app,
    resources={r"/api/*": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"

    return response



## Conectar a Base de datos
@app.route("/api/test")
def test():
    return jsonify({
        "message": "Backend funcionando"
    })

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "certificados")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_WRITE_LOCK = threading.Lock()

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.OperationalError:
        pass
    conn.row_factory = sqlite3.Row
    return conn

def ensure_database_schema():
    conn = get_db()
    cursor = conn.cursor()

    for nombre, definicion in (
        ("perfil_foto", "TEXT DEFAULT ''"),
        ("perfil_speech", "TEXT DEFAULT ''"),
        ("perfil_materias", "TEXT DEFAULT '[]'"),
    ):
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {nombre} {definicion}")
        except sqlite3.OperationalError:
            pass

    for nombre, definicion in (
        ("reporte_conflicto", "TEXT DEFAULT ''"),
        ("fecha_conflicto", "TEXT DEFAULT ''"),
    ):
        try:
            cursor.execute(f"ALTER TABLE reservas ADD COLUMN {nombre} {definicion}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT DEFAULT '',
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER NOT NULL,
        user2_id INTEGER NOT NULL,
        user1_label TEXT DEFAULT '',
        user2_label TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user1_id) REFERENCES users(id),
        FOREIGN KEY(user2_id) REFERENCES users(id)
    )
    """)

    for nombre, definicion in (
        ("user1_label", "TEXT DEFAULT ''"),
        ("user2_label", "TEXT DEFAULT ''"),
    ):
        try:
            cursor.execute(f"ALTER TABLE conversations ADD COLUMN {nombre} {definicion}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@loop.com",))

    if not cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO users (
                username,
                email,
                password,
                tokens,
                intentos_fallidos,
                bloqueado,
                rol
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Admin Loop",
                "admin@loop.com",
                generate_password_hash("admin123"),
                0,
                0,
                0,
                "admin",
            )
        )

    for old_id, new_id, nombre in (
        (1, 1001, "Gabriel Avila"),
        (2, 1002, "Maximo Barraza"),
        (3, 1003, "Tomas Tagliani"),
        (4, 1004, "Abril Cejas"),
        (5, 1005, "Franco Gallardo"),
        (6, 1006, "Lautaro Rodriguez"),
    ):
        cursor.execute(
            """
            UPDATE reservas
            SET profesor_id = ?
            WHERE profesor_id = ?
            AND profesor_nombre = ?
            """,
            (new_id, old_id, nombre)
        )

        cursor.execute(
            """
            UPDATE disponibilidades
            SET profesor_id = ?
            WHERE id IN (
                SELECT disponibilidad_id
                FROM reservas
                WHERE profesor_id = ?
                AND profesor_nombre = ?
            )
            """,
            (new_id, new_id, nombre)
        )

        cursor.execute(
            """
            UPDATE conversations
            SET user1_id = ?
            WHERE user1_id = ?
            AND user1_label = ?
            """,
            (new_id, old_id, nombre)
        )

        cursor.execute(
            """
            UPDATE conversations
            SET user2_id = ?
            WHERE user2_id = ?
            AND user2_label = ?
            """,
            (new_id, old_id, nombre)
        )

    cursor.execute(
        """
        UPDATE users
        SET rol = 'alumno'
        WHERE rol = 'profe'
        AND id IN (
            SELECT user_id
            FROM profesor_postulaciones
            WHERE estado != 'aprobada'
        )
        """
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id),
        FOREIGN KEY(sender_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

ensure_database_schema()

def get_user_id_from_token():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    if not token.startswith("token-demo-"):
        return None

    try:
        return int(token.replace("token-demo-", ""))
    except ValueError:
        return None

def serializar_postulacion(row):
    if not row:
        return None

    return {
        "id": row["id"],
        "userId": row["user_id"],
        "materia": row["materia"],
        "descripcion": row["descripcion"],
        "dias": json.loads(row["dias"] or "[]"),
        "horarios": json.loads(row["horarios"] or "[]"),
        "certificadoNombre": row["certificado_nombre"],
        "certificadoPath": row["certificado_path"],
        "estado": row["estado"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }

def crear_notificacion(cursor, user_id, title, body="", tipo="info"):
    if not user_id:
        return

    cursor.execute(
        """
        INSERT INTO notifications (user_id, title, body, type)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, title, body, tipo)
    )

def serializar_notificacion(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "type": row["type"],
        "isRead": bool(row["is_read"]),
        "createdAt": row["created_at"],
    }

def get_or_create_conversation(cursor, user1_id, user2_id, user1_label="", user2_label=""):
    if user1_id == user2_id:
        return None

    cursor.execute(
        """
        SELECT id, user1_label, user2_label
        FROM conversations
        WHERE (user1_id = ? AND user2_id = ?)
        OR (user1_id = ? AND user2_id = ?)
        """,
        (user1_id, user2_id, user2_id, user1_id)
    )

    conversation = cursor.fetchone()

    if conversation:
        if user1_label or user2_label:
            cursor.execute(
                """
                UPDATE conversations
                SET user1_label = COALESCE(NULLIF(user1_label, ''), ?),
                    user2_label = COALESCE(NULLIF(user2_label, ''), ?)
                WHERE id = ?
                """,
                (user1_label, user2_label, conversation["id"])
            )
        return conversation["id"]

    cursor.execute(
        """
        INSERT INTO conversations (user1_id, user2_id, user1_label, user2_label)
        VALUES (?, ?, ?, ?)
        """,
        (user1_id, user2_id, user1_label, user2_label)
    )

    return cursor.lastrowid

def serializar_mensaje(row):
    return {
        "id": row["id"],
        "conversationId": row["conversation_id"],
        "senderId": row["sender_id"],
        "content": row["content"],
        "isRead": bool(row["is_read"]),
        "createdAt": row["created_at"],
        "senderName": row["sender_name"],
    }

def serializar_usuario(row):
    materias = []

    try:
        materias = json.loads(row["perfil_materias"] or "[]")
    except (json.JSONDecodeError, TypeError):
        materias = []

    return {
        "id": row["id"],
        "nombre": row["username"],
        "email": row["email"],
        "tokens": row["tokens"],
        "rol": row["rol"],
        "perfil": {
            "foto": row["perfil_foto"] or "",
            "speech": row["perfil_speech"] or "",
            "materias": materias if isinstance(materias, list) else [],
        }
    }

def is_admin_user(user_id):
    if not user_id:
        return False

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT rol FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return bool(user and user["rol"] == "admin")

def serializar_profesor_aprobado(row):
    try:
        dias = json.loads(row["dias"] or "[]")
    except (json.JSONDecodeError, TypeError):
        dias = []

    try:
        horarios = json.loads(row["horarios"] or "[]")
    except (json.JSONDecodeError, TypeError):
        horarios = []

    disponibilidad = [
        {
            "dia": str(dia).capitalize(),
            "horarios": horarios,
        }
        for dia in dias
    ]

    materias = [row["materia"]] if row["materia"] else []

    return {
        "id": row["user_id"],
        "postulacionId": row["id"],
        "nombre": row["username"],
        "email": row["email"],
        "rating": row["rating_promedio"] or 0,
        "ratingCantidad": row["rating_cantidad"] or 0,
        "materias": materias,
        "imagen": row["perfil_foto"] or "",
        "descripcion": row["perfil_speech"] or row["descripcion"],
        "disponibilidad": disponibilidad,
        "certificadoNombre": row["certificado_nombre"],
        "estado": row["estado"],
    }

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

@app.route("/api/recuperacion", methods=["POST"])
def api_solicitar_recuperacion():
    data = request.get_json()
    email = (data.get("email") if data else "") or ""
    email = email.strip().lower()

    if not email:
        return jsonify({"mensaje": "Ingresa un email valido."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()

    codigo_demo = None

    if user:
        codigo_demo = f"{secrets.randbelow(900000) + 100000}"
        expires_at = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0",
            (user["id"],)
        )

        cursor.execute(
            """
            INSERT INTO password_resets (user_id, code, expires_at, used)
            VALUES (?, ?, ?, 0)
            """,
            (user["id"], codigo_demo, expires_at)
        )

        conn.commit()

    conn.close()

    response = {
        "mensaje": "Si el correo esta registrado, se genero un codigo de recuperacion."
    }

    if codigo_demo:
        response["codigo_demo"] = codigo_demo

    return jsonify(response), 200

@app.route("/api/recuperacion/reset", methods=["POST"])
def api_confirmar_recuperacion():
    data = request.get_json()

    if not data:
        return jsonify({"mensaje": "Faltan datos para restablecer la contrasena."}), 400

    email = (data.get("email") or "").strip().lower()
    codigo = (data.get("codigo") or "").strip()
    nueva_password = data.get("password") or ""

    if not email or not codigo or not nueva_password:
        return jsonify({"mensaje": "Completa email, codigo y nueva contrasena."}), 400

    if len(nueva_password) < 6:
        return jsonify({"mensaje": "La nueva contrasena debe tener al menos 6 caracteres."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"mensaje": "Codigo invalido o vencido."}), 400

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT id
        FROM password_resets
        WHERE user_id = ?
        AND code = ?
        AND used = 0
        AND expires_at >= ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user["id"], codigo, ahora)
    )

    reset = cursor.fetchone()

    if not reset:
        conn.close()
        return jsonify({"mensaje": "Codigo invalido o vencido."}), 400

    password_hash = generate_password_hash(nueva_password)

    cursor.execute(
        """
        UPDATE users
        SET password = ?,
            intentos_fallidos = 0,
            bloqueado = 0
        WHERE id = ?
        """,
        (password_hash, user["id"])
    )

    cursor.execute(
        "UPDATE password_resets SET used = 1 WHERE id = ?",
        (reset["id"],)
    )

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Contrasena actualizada correctamente."}), 200

@app.route("/api/notificaciones", methods=["GET"])
def api_get_notificaciones():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, body, type, is_read, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (user_id,)
    )

    notificaciones = cursor.fetchall()
    conn.close()

    return jsonify({
        "notificaciones": [
            serializar_notificacion(notificacion)
            for notificacion in notificaciones
        ]
    }), 200

@app.route("/api/conversaciones", methods=["GET"])
def api_get_conversaciones():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            c.id,
            CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END AS other_user_id,
            COALESCE(
                u.username,
                NULLIF(CASE WHEN c.user1_id = ? THEN c.user2_label ELSE c.user1_label END, ''),
                'Usuario Loop'
            ) AS other_user_name,
            (
                SELECT content
                FROM messages m
                WHERE m.conversation_id = c.id
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message,
            (
                SELECT created_at
                FROM messages m
                WHERE m.conversation_id = c.id
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message_at
        FROM conversations c
        LEFT JOIN users u
          ON u.id = CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END
        WHERE (c.user1_id = ? OR c.user2_id = ?)
        AND c.user1_id != c.user2_id
        AND EXISTS (
            SELECT 1
            FROM messages m
            WHERE m.conversation_id = c.id
        )
        ORDER BY COALESCE(last_message_at, c.created_at) DESC
        """,
        (user_id, user_id, user_id, user_id, user_id)
    )

    conversaciones = cursor.fetchall()
    conn.close()

    return jsonify({
        "conversaciones": [
            {
                "id": row["id"],
                "otherUserId": row["other_user_id"],
                "otherUserName": row["other_user_name"],
                "lastMessage": row["last_message"] or "Sin mensajes todavia.",
                "lastMessageAt": row["last_message_at"],
            }
            for row in conversaciones
        ]
    }), 200

@app.route("/api/conversaciones", methods=["POST"])
def api_create_conversacion():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    data = request.get_json()

    try:
        other_user_id = int(data.get("user_id") if data else 0)
    except (TypeError, ValueError):
        return jsonify({"mensaje": "Usuario destino invalido."}), 400

    other_user_name = ((data.get("user_name") if data else "") or "Profesor Loop").strip()
    current_user_name = ((data.get("current_user_name") if data else "") or "Usuario Loop").strip()

    if not other_user_id or other_user_id == user_id:
        return jsonify({"mensaje": "Usuario destino invalido."}), 400

    conn = get_db()
    cursor = conn.cursor()

    conversation_id = get_or_create_conversation(
        cursor,
        user_id,
        other_user_id,
        current_user_name,
        other_user_name
    )

    if not conversation_id:
        conn.close()
        return jsonify({"mensaje": "No se puede crear una conversacion con tu propio usuario."}), 400

    conn.commit()
    conn.close()

    return jsonify({"conversationId": conversation_id}), 200

@app.route("/api/conversaciones/<int:conversation_id>/mensajes", methods=["GET"])
def api_get_mensajes_conversacion(conversation_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM conversations
        WHERE id = ?
        AND (user1_id = ? OR user2_id = ?)
        """,
        (conversation_id, user_id, user_id)
    )

    conversation = cursor.fetchone()

    if not conversation:
        conn.close()
        return jsonify({"mensaje": "Conversacion no encontrada."}), 404

    cursor.execute(
        """
        UPDATE messages
        SET is_read = 1
        WHERE conversation_id = ?
        AND sender_id != ?
        """,
        (conversation_id, user_id)
    )

    cursor.execute(
        """
        SELECT
            m.id,
            m.conversation_id,
            m.sender_id,
            m.content,
            m.is_read,
            m.created_at,
            COALESCE(u.username, 'Usuario Loop') AS sender_name
        FROM messages m
        LEFT JOIN users u ON u.id = m.sender_id
        WHERE m.conversation_id = ?
        ORDER BY m.id ASC
        """,
        (conversation_id,)
    )

    mensajes = cursor.fetchall()
    conn.commit()
    conn.close()

    return jsonify({
        "mensajes": [serializar_mensaje(mensaje) for mensaje in mensajes]
    }), 200

@app.route("/api/conversaciones/<int:conversation_id>/mensajes", methods=["POST"])
def api_send_mensaje_conversacion(conversation_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    data = request.get_json()
    content = (data.get("content") if data else "") or ""
    content = content.strip()

    if not content:
        return jsonify({"mensaje": "El mensaje no puede estar vacio."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user1_id, user2_id
        FROM conversations
        WHERE id = ?
        AND (user1_id = ? OR user2_id = ?)
        """,
        (conversation_id, user_id, user_id)
    )

    conversation = cursor.fetchone()

    if not conversation:
        conn.close()
        return jsonify({"mensaje": "Conversacion no encontrada."}), 404

    cursor.execute(
        """
        INSERT INTO messages (conversation_id, sender_id, content)
        VALUES (?, ?, ?)
        """,
        (conversation_id, user_id, content)
    )

    receiver_id = conversation["user2_id"] if conversation["user1_id"] == user_id else conversation["user1_id"]

    crear_notificacion(
        cursor,
        receiver_id,
        "Nuevo mensaje",
        content,
        "mensaje"
    )

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Mensaje enviado correctamente."}), 201

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

    certificado = request.files["certificado"]

    if not certificado or certificado.filename == "":
        return jsonify({"mensaje": "Adjuntá el certificado de materias aprobadas."}), 400

    certificado_nombre = secure_filename(certificado.filename)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    nombre_archivo = f"user_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{certificado_nombre}"
    certificado_path = os.path.join(UPLOAD_DIR, nombre_archivo)
    certificado.save(certificado_path)

    cursor.execute(
        """
        INSERT INTO profesor_postulaciones (
            user_id,
            materia,
            descripcion,
            dias,
            horarios,
            certificado_nombre,
            certificado_path,
            estado,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            materia = excluded.materia,
            descripcion = excluded.descripcion,
            dias = excluded.dias,
            horarios = excluded.horarios,
            certificado_nombre = excluded.certificado_nombre,
            certificado_path = excluded.certificado_path,
            estado = 'pendiente',
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            materia,
            descripcion,
            json.dumps(dias, ensure_ascii=False),
            json.dumps(horarios, ensure_ascii=False),
            certificado_nombre,
            certificado_path,
        )
    )

    crear_notificacion(
        cursor,
        user_id,
        "Postulacion enviada",
        f"Tu perfil como profe para {materia} quedo pendiente de revision.",
        "postulacion"
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM profesor_postulaciones
        WHERE user_id = ?
        """,
        (user_id,)
    )

    postulacion = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Postulación enviada correctamente.",
        "postulacion": serializar_postulacion(postulacion)
    }), 200

@app.route("/api/profesores", methods=["GET"])
def api_get_profesores_aprobados():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            p.*,
            u.username,
            u.email,
            u.perfil_foto,
            u.perfil_speech,
            ROUND(AVG(r.stars), 1) AS rating_promedio,
            COUNT(r.id) AS rating_cantidad
        FROM profesor_postulaciones p
        INNER JOIN users u ON u.id = p.user_id
        LEFT JOIN ratings r ON r.rated_user_id = p.user_id
        WHERE p.estado = 'aprobada'
        GROUP BY p.id
        ORDER BY p.updated_at DESC
        """
    )

    profesores = cursor.fetchall()
    conn.close()

    return jsonify({
        "profesores": [serializar_profesor_aprobado(profesor) for profesor in profesores]
    }), 200

@app.route("/api/admin/postulaciones", methods=["GET"])
def api_admin_get_postulaciones():
    user_id = get_user_id_from_token()

    if not is_admin_user(user_id):
        return jsonify({"mensaje": "No tenes permisos de administrador."}), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            p.*,
            u.username,
            u.email,
            u.perfil_foto,
            u.perfil_speech,
            0 AS rating_promedio,
            0 AS rating_cantidad
        FROM profesor_postulaciones p
        INNER JOIN users u ON u.id = p.user_id
        ORDER BY
            CASE p.estado
                WHEN 'pendiente' THEN 0
                WHEN 'aprobada' THEN 1
                ELSE 2
            END,
            p.updated_at DESC
        """
    )

    postulaciones = cursor.fetchall()
    conn.close()

    return jsonify({
        "postulaciones": [
            serializar_profesor_aprobado(postulacion)
            for postulacion in postulaciones
        ]
    }), 200

@app.route("/api/admin/postulaciones/<int:postulacion_id>/aprobar", methods=["PATCH"])
def api_admin_aprobar_postulacion(postulacion_id):
    admin_id = get_user_id_from_token()

    if not is_admin_user(admin_id):
        return jsonify({"mensaje": "No tenes permisos de administrador."}), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profesor_postulaciones WHERE id = ?", (postulacion_id,))
    postulacion = cursor.fetchone()

    if not postulacion:
        conn.close()
        return jsonify({"mensaje": "Postulacion no encontrada."}), 404

    cursor.execute(
        """
        UPDATE profesor_postulaciones
        SET estado = 'aprobada',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (postulacion_id,)
    )

    cursor.execute(
        """
        UPDATE users
        SET rol = 'profe',
            perfil_speech = COALESCE(NULLIF(perfil_speech, ''), ?),
            perfil_materias = ?
        WHERE id = ?
        """,
        (
            postulacion["descripcion"],
            json.dumps([postulacion["materia"]], ensure_ascii=False),
            postulacion["user_id"],
        )
    )

    crear_notificacion(
        cursor,
        postulacion["user_id"],
        "Postulacion aprobada",
        "Tu perfil de profesor ya esta visible en Loop.",
        "postulacion"
    )

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Postulacion aprobada correctamente."}), 200

@app.route("/api/admin/postulaciones/<int:postulacion_id>/rechazar", methods=["PATCH"])
def api_admin_rechazar_postulacion(postulacion_id):
    admin_id = get_user_id_from_token()

    if not is_admin_user(admin_id):
        return jsonify({"mensaje": "No tenes permisos de administrador."}), 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profesor_postulaciones WHERE id = ?", (postulacion_id,))
    postulacion = cursor.fetchone()

    if not postulacion:
        conn.close()
        return jsonify({"mensaje": "Postulacion no encontrada."}), 404

    cursor.execute(
        """
        UPDATE profesor_postulaciones
        SET estado = 'rechazada',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (postulacion_id,)
    )

    cursor.execute(
        """
        UPDATE users
        SET rol = 'alumno'
        WHERE id = ?
        """,
        (postulacion["user_id"],)
    )

    crear_notificacion(
        cursor,
        postulacion["user_id"],
        "Postulacion rechazada",
        "Tu solicitud para ser profesor necesita revision.",
        "postulacion"
    )

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Postulacion rechazada correctamente."}), 200

@app.route("/api/ratings", methods=["POST"])
def api_create_rating():
    reviewer_id = get_user_id_from_token()

    if not reviewer_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    data = request.get_json()

    if not data:
        return jsonify({"mensaje": "Faltan datos de calificación."}), 400

    rated_user_id = data.get("rated_user_id")
    stars = data.get("stars")
    comment = data.get("comment", "")
    reserva_id = data.get("reserva_id")

    try:
        rated_user_id = int(rated_user_id)
        stars = int(stars)
    except (TypeError, ValueError):
        return jsonify({"mensaje": "La calificación enviada no es válida."}), 400

    if stars < 1 or stars > 5:
        return jsonify({"mensaje": "La calificación debe ser de 1 a 5 estrellas."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM ratings
        WHERE reviewer_id = ?
        AND rated_user_id = ?
        """,
        (reviewer_id, rated_user_id)
    )

    existing_rating = cursor.fetchone()

    if existing_rating:
        cursor.execute(
            """
            UPDATE ratings
            SET stars = ?, comment = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (stars, comment, existing_rating["id"])
        )
    else:
        cursor.execute(
            """
            INSERT INTO ratings (reviewer_id, rated_user_id, stars, comment)
            VALUES (?, ?, ?, ?)
            """,
            (reviewer_id, rated_user_id, stars, comment)
        )

    if reserva_id:
        try:
            reserva_id = int(reserva_id)
            cursor.execute(
                """
                UPDATE reservas
                SET estado = 'CALIFICADA'
                WHERE id = ?
                AND alumno_id = ?
                """,
                (reserva_id, reviewer_id)
            )
        except (TypeError, ValueError):
            pass

    conn.commit()

    cursor.execute(
        """
        SELECT ROUND(AVG(stars), 1) AS promedio, COUNT(*) AS cantidad
        FROM ratings
        WHERE rated_user_id = ?
        """,
        (rated_user_id,)
    )

    summary = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Calificación guardada correctamente.",
        "rating": {
            "rated_user_id": rated_user_id,
            "promedio": summary["promedio"] or 0,
            "cantidad": summary["cantidad"]
        }
    }), 201

@app.route("/api/reservas/para-calificar", methods=["GET"])
def api_get_reserva_para_calificar():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            r.*,
            a.confirmacion_alumno,
            a.confirmacion_profesor,
            a.fecha_confirmacion,
            r.profesor_id AS target_user_id,
            r.profesor_nombre AS target_user_name,
            'alumno' AS rol_en_reserva
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        LEFT JOIN users u ON u.id = r.alumno_id
        WHERE r.alumno_id = ?
        AND r.estado IN ('COMPLETADA', 'CALIFICADA')
        AND NOT EXISTS (
            SELECT 1
            FROM ratings rt
            WHERE rt.reviewer_id = ?
            AND rt.rated_user_id = r.profesor_id
        )
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (user_id, user_id)
    )

    reserva = cursor.fetchone()
    conn.close()

    if not reserva:
        return jsonify({"reserva": None}), 200

    reserva_serializada = serialize_reserva(reserva)
    reserva_serializada["targetUserId"] = reserva["target_user_id"]
    reserva_serializada["targetUserName"] = reserva["target_user_name"]
    reserva_serializada["rolEnReserva"] = reserva["rol_en_reserva"]

    return jsonify({"reserva": reserva_serializada}), 200

@app.route("/api/ratings/reserva", methods=["POST"])
def api_create_rating_reserva():
    reviewer_id = get_user_id_from_token()

    if not reviewer_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    data = request.get_json()

    if not data:
        return jsonify({"mensaje": "Faltan datos de calificacion."}), 400

    try:
        reserva_id = int(data.get("reserva_id"))
        rated_user_id = int(data.get("rated_user_id"))
        stars = int(data.get("stars"))
    except (TypeError, ValueError):
        return jsonify({"mensaje": "La calificacion enviada no es valida."}), 400

    comment = data.get("comment", "")

    if stars < 1 or stars > 5:
        return jsonify({"mensaje": "La calificacion debe ser de 1 a 5 estrellas."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, alumno_id, profesor_id, profesor_nombre, estado
        FROM reservas
        WHERE id = ?
        AND alumno_id = ?
        AND estado IN ('COMPLETADA', 'CALIFICADA')
        """,
        (reserva_id, reviewer_id)
    )

    reserva = cursor.fetchone()

    if not reserva:
        conn.close()
        return jsonify({"mensaje": "No encontramos una reserva completada para calificar."}), 404

    expected_rated_user_id = reserva["profesor_id"]

    if rated_user_id != expected_rated_user_id:
        conn.close()
        return jsonify({"mensaje": "La calificacion no coincide con la reserva."}), 400

    cursor.execute(
        """
        SELECT id
        FROM ratings
        WHERE reviewer_id = ?
        AND rated_user_id = ?
        """,
        (reviewer_id, rated_user_id)
    )

    existing_rating = cursor.fetchone()

    if existing_rating:
        cursor.execute(
            """
            UPDATE ratings
            SET stars = ?, comment = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (stars, comment, existing_rating["id"])
        )
    else:
        cursor.execute(
            """
            INSERT INTO ratings (reviewer_id, rated_user_id, stars, comment)
            VALUES (?, ?, ?, ?)
            """,
            (reviewer_id, rated_user_id, stars, comment)
        )

    cursor.execute(
        "UPDATE reservas SET estado = 'CALIFICADA' WHERE id = ?",
        (reserva["id"],)
    )

    cursor.execute(
        """
        UPDATE notifications
        SET title = 'Clase calificada',
            body = 'Tu calificacion fue registrada correctamente.',
            type = 'calificacion'
        WHERE user_id = ?
        AND type = 'validacion'
        AND body LIKE ?
        """,
        (reviewer_id, f"%{reserva['profesor_nombre']}%")
    )

    conn.commit()

    cursor.execute(
        """
        SELECT ROUND(AVG(stars), 1) AS promedio, COUNT(*) AS cantidad
        FROM ratings
        WHERE rated_user_id = ?
        """,
        (rated_user_id,)
    )

    summary = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Calificacion guardada correctamente.",
        "rating": {
            "rated_user_id": rated_user_id,
            "promedio": summary["promedio"] or 0,
            "cantidad": summary["cantidad"]
        }
    }), 201

@app.route("/api/ratings/<int:user_id>", methods=["GET"])
def api_get_rating(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ROUND(AVG(stars), 1) AS promedio, COUNT(*) AS cantidad
        FROM ratings
        WHERE rated_user_id = ?
        """,
        (user_id,)
    )

    summary = cursor.fetchone()
    conn.close()

    return jsonify({
        "rated_user_id": user_id,
        "promedio": summary["promedio"] or 0,
        "cantidad": summary["cantidad"]
    }), 200

def get_or_create_disponibilidad(cursor, profesor_id, turno):
    partes = str(turno).split()
    fecha = partes[0] if partes else "Sin fecha"
    hora_inicio = partes[1] if len(partes) > 1 else "00:00"

    try:
        hora_fin = (
            datetime.strptime(hora_inicio, "%H:%M") + timedelta(hours=1)
        ).strftime("%H:%M")
    except ValueError:
        hora_fin = hora_inicio

    cursor.execute(
        """
        SELECT id
        FROM disponibilidades
        WHERE profesor_id = ?
        AND fecha = ?
        AND hora_inicio = ?
        """,
        (profesor_id, fecha, hora_inicio)
    )

    disponibilidad = cursor.fetchone()

    if disponibilidad:
        return disponibilidad["id"]

    cursor.execute(
        """
        INSERT INTO disponibilidades (profesor_id, fecha, hora_inicio, hora_fin)
        VALUES (?, ?, ?, ?)
        """,
        (profesor_id, fecha, hora_inicio, hora_fin)
    )

    return cursor.lastrowid

def serialize_reserva(row):
    return {
        "id": row["id"],
        "alumnoId": row["alumno_id"],
        "profesorId": row["profesor_id"],
        "profesorNombre": row["profesor_nombre"],
        "turno": row["turno"],
        "estado": row["estado"],
        "meet": row["meet"],
        "checkAlumno": bool(row["confirmacion_alumno"]),
        "checkProfesor": bool(row["confirmacion_profesor"]),
        "fechaConfirmacion": row["fecha_confirmacion"],
        "reporteConflicto": row["reporte_conflicto"],
        "fechaConflicto": row["fecha_conflicto"],
    }

def serialize_reserva_for_user(row, user_id):
    reserva = serialize_reserva(row)
    reserva["rolEnReserva"] = (
        "alumno" if row["alumno_id"] == user_id else "profesor"
    )
    return reserva

@app.route("/api/reservas", methods=["POST"])
def api_create_reserva():
    alumno_id = get_user_id_from_token()

    if not alumno_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    data = request.get_json()

    if not data:
        return jsonify({"mensaje": "Faltan datos de reserva."}), 400

    try:
        profesor_id = int(data.get("profesor_id"))
    except (TypeError, ValueError):
        return jsonify({"mensaje": "Profesor inválido."}), 400

    profesor_nombre = data.get("profesor_nombre") or "Profesor Loop"
    turno = data.get("turno")
    meet = data.get("meet") or "https://meet.google.com/demo-loop"

    if not turno:
        return jsonify({"mensaje": "Seleccioná un turno."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT username, tokens FROM users WHERE id = ?", (alumno_id,))
    alumno = cursor.fetchone()

    if not alumno:
        conn.close()
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    if (alumno["tokens"] or 0) < 1:
        conn.close()
        return jsonify({"mensaje": "No tenés tokens suficientes para reservar."}), 400

    disponibilidad_id = get_or_create_disponibilidad(cursor, profesor_id, turno)

    cursor.execute(
        """
        SELECT id
        FROM reservas
        WHERE disponibilidad_id = ?
        AND estado = 'ACTIVA'
        """,
        (disponibilidad_id,)
    )

    if cursor.fetchone():
        conn.close()
        return jsonify({"mensaje": "Ese horario ya fue reservado."}), 409

    fecha_reserva = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO reservas (
            disponibilidad_id,
            alumno_id,
            profesor_id,
            profesor_nombre,
            turno,
            estado,
            meet,
            fecha_reserva
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            disponibilidad_id,
            alumno_id,
            profesor_id,
            profesor_nombre,
            turno,
            "ACTIVA",
            meet,
            fecha_reserva,
        )
    )

    reserva_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO asistencias (reserva_id, confirmacion_alumno, confirmacion_profesor)
        VALUES (?, 0, 0)
        """,
        (reserva_id,)
    )

    cursor.execute(
        "UPDATE users SET tokens = tokens - 1 WHERE id = ?",
        (alumno_id,)
    )

    crear_notificacion(
        cursor,
        alumno_id,
        "Reserva confirmada",
        f"Intercambiaste 1 token por una clase con {profesor_nombre}. Turno: {turno}.",
        "reserva"
    )

    conversation_id = get_or_create_conversation(
        cursor,
        alumno_id,
        profesor_id,
        alumno["username"] if alumno else "Alumno Loop",
        profesor_nombre
    )

    if conversation_id:
        cursor.execute(
            """
            INSERT INTO messages (conversation_id, sender_id, content)
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                alumno_id,
                f"Hola, reserve una clase para {turno}. El link externo es {meet}.",
            )
        )

    conn.commit()

    cursor.execute(
        """
        SELECT r.*, a.confirmacion_alumno, a.confirmacion_profesor, a.fecha_confirmacion
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        WHERE r.id = ?
        """,
        (reserva_id,)
    )

    reserva = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Reserva creada correctamente.",
        "reserva": serialize_reserva(reserva)
    }), 201

@app.route("/api/reservas/activa", methods=["GET"])
def api_get_reserva_activa():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.*, a.confirmacion_alumno, a.confirmacion_profesor, a.fecha_confirmacion
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        WHERE (r.alumno_id = ? OR r.profesor_id = ?)
        AND r.estado IN ('ACTIVA', 'COMPLETADA', 'EN_CONFLICTO')
        AND (
            r.estado != 'COMPLETADA'
            OR NOT EXISTS (
                SELECT 1
                FROM ratings rt
                WHERE rt.reviewer_id = ?
                AND rt.rated_user_id = CASE
                    WHEN r.alumno_id = ? THEN r.profesor_id
                    ELSE r.alumno_id
                END
            )
        )
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (user_id, user_id, user_id, user_id)
    )

    reserva = cursor.fetchone()
    conn.close()

    if not reserva:
        return jsonify({"reserva": None}), 200

    return jsonify({"reserva": serialize_reserva_for_user(reserva, user_id)}), 200

@app.route("/api/reservas/proxima", methods=["GET"])
def api_get_reserva_proxima():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token invalido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.*, a.confirmacion_alumno, a.confirmacion_profesor, a.fecha_confirmacion
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        WHERE (r.alumno_id = ? OR r.profesor_id = ?)
        AND r.estado IN ('ACTIVA', 'EN_CONFLICTO')
        ORDER BY r.id DESC
        LIMIT 1
        """,
        (user_id, user_id)
    )

    reserva = cursor.fetchone()
    conn.close()

    if not reserva:
        return jsonify({"reserva": None}), 200

    return jsonify({"reserva": serialize_reserva_for_user(reserva, user_id)}), 200

@app.route("/api/reservas/<int:reserva_id>/cancelar", methods=["PATCH"])
def api_cancel_reserva(reserva_id):
    alumno_id = get_user_id_from_token()

    if not alumno_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, estado
        FROM reservas
        WHERE id = ?
        AND alumno_id = ?
        """,
        (reserva_id, alumno_id)
    )

    reserva = cursor.fetchone()

    if not reserva:
        conn.close()
        return jsonify({"mensaje": "Reserva no encontrada."}), 404

    if reserva["estado"] == "CANCELADA":
        conn.close()
        return jsonify({"mensaje": "La reserva ya está cancelada."}), 400

    if reserva["estado"] not in ("ACTIVA", "EN_CONFLICTO"):
        conn.close()
        return jsonify({"mensaje": "Esta reserva ya no se puede cancelar."}), 400

    cursor.execute("UPDATE reservas SET estado = 'CANCELADA' WHERE id = ?", (reserva_id,))
    cursor.execute("UPDATE users SET tokens = tokens + 1 WHERE id = ?", (alumno_id,))
    cursor.execute("SELECT username, tokens FROM users WHERE id = ?", (alumno_id,))
    usuario = cursor.fetchone()

    crear_notificacion(
        cursor,
        alumno_id,
        "Reserva cancelada",
        "La reserva fue cancelada y recuperaste 1 token.",
        "cancelacion"
    )

    conn.commit()
    conn.close()

    return jsonify({
        "mensaje": "Reserva cancelada correctamente.",
        "tokens": usuario["tokens"] if usuario else None
    }), 200

@app.route("/api/reservas/<int:reserva_id>/conflicto", methods=["PATCH"])
def api_reportar_conflicto(reserva_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    data = request.get_json(silent=True) or {}
    motivo = (data.get("motivo") or "Una de las partes no se presentó.").strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, estado, alumno_id
        FROM reservas
        WHERE id = ?
        AND (alumno_id = ? OR profesor_id = ?)
        """,
        (reserva_id, user_id, user_id)
    )

    reserva = cursor.fetchone()

    if not reserva:
        conn.close()
        return jsonify({"mensaje": "Reserva no encontrada."}), 404

    if reserva["estado"] != "ACTIVA":
        conn.close()
        return jsonify({"mensaje": "Solo se puede reportar conflicto en una reserva activa."}), 400

    fecha_conflicto = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        UPDATE reservas
        SET estado = 'EN_CONFLICTO',
            reporte_conflicto = ?,
            fecha_conflicto = ?
        WHERE id = ?
        """,
        (motivo, fecha_conflicto, reserva_id)
    )

    crear_notificacion(
        cursor,
        reserva["alumno_id"],
        "Reserva en conflicto",
        motivo,
        "conflicto"
    )

    conn.commit()

    cursor.execute(
        """
        SELECT r.*, a.confirmacion_alumno, a.confirmacion_profesor, a.fecha_confirmacion
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        WHERE r.id = ?
        """,
        (reserva_id,)
    )

    reserva_actualizada = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Reporte enviado correctamente.",
        "reserva": serialize_reserva(reserva_actualizada)
    }), 200

def confirmar_reserva(reserva_id, campo, user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, alumno_id, profesor_id, profesor_nombre, estado FROM reservas WHERE id = ?",
        (reserva_id,)
    )
    reserva_base = cursor.fetchone()

    if not reserva_base:
        conn.close()
        return None, ("Reserva no encontrada.", 404)

    if reserva_base["estado"] in ("CANCELADA", "CALIFICADA"):
        conn.close()
        return None, ("La reserva ya no admite cambios de asistencia.", 400)

    profesor_demo = (reserva_base["profesor_id"] or 0) >= 1000

    if campo == "confirmacion_alumno" and reserva_base["alumno_id"] != user_id:
        conn.close()
        return None, ("Solo el alumno de la reserva puede confirmar esa asistencia.", 403)

    if (
        campo == "confirmacion_profesor"
        and reserva_base["profesor_id"] != user_id
        and not (profesor_demo and reserva_base["alumno_id"] == user_id)
    ):
        conn.close()
        return None, ("Solo el profesor de la reserva puede confirmar esa asistencia.", 403)

    cursor.execute("SELECT * FROM asistencias WHERE reserva_id = ?", (reserva_id,))
    asistencia = cursor.fetchone()

    if not asistencia:
        conn.close()
        return None, ("Asistencia no encontrada.", 404)

    if asistencia[campo] == 1:
        conn.close()
        return None, ("Esa asistencia ya fue confirmada.", 400)

    cursor.execute(
        f"UPDATE asistencias SET {campo} = 1 WHERE reserva_id = ?",
        (reserva_id,)
    )

    conn.commit()

    cursor.execute("SELECT * FROM asistencias WHERE reserva_id = ?", (reserva_id,))
    asistencia = cursor.fetchone()

    if (
        asistencia["confirmacion_alumno"] == 1
        and asistencia["confirmacion_profesor"] == 1
        and asistencia["fecha_confirmacion"] is None
    ):
        fecha_confirmacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "UPDATE asistencias SET fecha_confirmacion = ? WHERE reserva_id = ?",
            (fecha_confirmacion, reserva_id)
        )

        cursor.execute(
            "UPDATE reservas SET estado = 'COMPLETADA' WHERE id = ?",
            (reserva_id,)
        )

        cursor.execute("SELECT alumno_id, profesor_id, profesor_nombre FROM reservas WHERE id = ?", (reserva_id,))
        reserva = cursor.fetchone()

        if reserva:
            cursor.execute(
                "UPDATE users SET tokens = tokens + 1 WHERE id = ?",
                (reserva["profesor_id"],)
            )

            crear_notificacion(
                cursor,
                reserva["alumno_id"],
                "Loop completado",
                f"La clase con {reserva['profesor_nombre']} fue validada. Ya podes calificarla.",
                "validacion"
            )

        conn.commit()

    cursor.execute(
        """
        SELECT r.*, a.confirmacion_alumno, a.confirmacion_profesor, a.fecha_confirmacion
        FROM reservas r
        INNER JOIN asistencias a ON a.reserva_id = r.id
        WHERE r.id = ?
        """,
        (reserva_id,)
    )

    reserva_actualizada = cursor.fetchone()
    conn.close()

    return serialize_reserva_for_user(reserva_actualizada, user_id), None

@app.route("/api/reservas/<int:reserva_id>/confirmar-alumno", methods=["PATCH"])
def api_confirmar_alumno(reserva_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    reserva, error = confirmar_reserva(reserva_id, "confirmacion_alumno", user_id)

    if error:
        mensaje, status = error
        return jsonify({"mensaje": mensaje}), status

    return jsonify({"mensaje": "Alumno confirmado correctamente.", "reserva": reserva}), 200

@app.route("/api/reservas/<int:reserva_id>/confirmar-profesor", methods=["PATCH"])
def api_confirmar_profesor(reserva_id):
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    reserva, error = confirmar_reserva(reserva_id, "confirmacion_profesor", user_id)

    if error:
        mensaje, status = error
        return jsonify({"mensaje": mensaje}), status

    return jsonify({"mensaje": "Profesor confirmado correctamente.", "reserva": reserva}), 200

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
        """
        SELECT
            id,
            username,
            email,
            tokens,
            rol,
            perfil_foto,
            perfil_speech,
            perfil_materias
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT *
        FROM profesor_postulaciones
        WHERE user_id = ?
        """,
        (user_id,)
    )

    postulacion = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    return jsonify({
        "usuario": serializar_usuario(user),
        "postulacion": serializar_postulacion(postulacion),
        "reservas": []
    }), 200

@app.route("/api/perfil", methods=["PUT"])
def api_update_perfil():
    user_id = get_user_id_from_token()

    if not user_id:
        return jsonify({"mensaje": "Token inválido o inexistente."}), 401

    data = request.get_json()

    if not data:
        return jsonify({"mensaje": "Faltan datos para actualizar el perfil."}), 400

    speech = (data.get("speech") or "").strip()
    foto = data.get("foto") or ""
    materias = data.get("materias") or []

    if speech and len(speech) < 10:
        return jsonify({"mensaje": "La presentación debe tener al menos 10 caracteres."}), 400

    if not isinstance(materias, list):
        return jsonify({"mensaje": "Las materias enviadas no son válidas."}), 400

    materias_limpias = [
        str(materia).strip()
        for materia in materias
        if str(materia).strip()
    ]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"mensaje": "Usuario no encontrado."}), 404

    cursor.execute(
        """
        UPDATE users
        SET perfil_foto = ?,
            perfil_speech = ?,
            perfil_materias = ?
        WHERE id = ?
        """,
        (
            foto,
            speech,
            json.dumps(materias_limpias, ensure_ascii=False),
            user_id,
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT
            id,
            username,
            email,
            tokens,
            rol,
            perfil_foto,
            perfil_speech,
            perfil_materias
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    usuario_actualizado = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Perfil actualizado correctamente.",
        "usuario": serializar_usuario(usuario_actualizado)
    }), 200

## Modo de Depuración
if __name__ == '__main__': 
    app.run(debug=True, threaded=False, use_reloader=False)
