import sqlite3
import os

print("CARPETA ACTUAL:")
print(os.getcwd())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
               
    id INTEGER PRIMARY KEY AUTOINCREMENT,
               
    username TEXT NOT NULL UNIQUE,
               
    email TEXT NOT NULL UNIQUE,
               
    password TEXT NOT NULL,

    tokens INTEGER DEFAULT 2,

    intentos_fallidos INTEGER DEFAULT 0,

    bloqueado INTEGER DEFAULT 0,

    rol TEXT DEFAULT 'alumno'
    
)
"""
)

for nombre, definicion in (
    ("tokens", "INTEGER DEFAULT 2"),
    ("intentos_fallidos", "INTEGER DEFAULT 0"),
    ("bloqueado", "INTEGER DEFAULT 0"),
    ("rol", "TEXT DEFAULT 'alumno'"),
):
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {nombre} {definicion}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""        
CREATE TABLE IF NOT EXISTS conversations (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user1_id INTEGER NOT NULL,

    user2_id INTEGER NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user1_id) REFERENCES users(id),
               
    FOREIGN KEY(user2_id) REFERENCES users(id)              
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reviewer_id INTEGER NOT NULL,

    rated_user_id INTEGER NOT NULL,

    stars INTEGER NOT NULL,

    comment TEXT DEFAULT '',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(reviewer_id) REFERENCES users(id),

    FOREIGN KEY(rated_user_id) REFERENCES users(id)

)
""")

for nombre, definicion in (
    ("comment", "TEXT DEFAULT ''"),
    ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
):
    try:
        cursor.execute(f"ALTER TABLE ratings ADD COLUMN {nombre} {definicion}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS profesor_postulaciones (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL UNIQUE,

    materia TEXT NOT NULL,

    descripcion TEXT NOT NULL,

    dias TEXT NOT NULL,

    horarios TEXT NOT NULL,

    certificado_nombre TEXT NOT NULL,

    certificado_path TEXT DEFAULT '',

    estado TEXT DEFAULT 'pendiente',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

)
""")

for nombre, definicion in (
    ("certificado_path", "TEXT DEFAULT ''"),
    ("estado", "TEXT DEFAULT 'pendiente'"),
    ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
):
    try:
        cursor.execute(f"ALTER TABLE profesor_postulaciones ADD COLUMN {nombre} {definicion}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS disponibilidades (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    profesor_id INTEGER NOT NULL,

    fecha TEXT NOT NULL,

    hora_inicio TEXT NOT NULL,

    hora_fin TEXT NOT NULL

)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reservas (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    disponibilidad_id INTEGER NOT NULL,

    alumno_id INTEGER NOT NULL,

    profesor_id INTEGER NOT NULL,

    profesor_nombre TEXT NOT NULL,

    turno TEXT NOT NULL,

    estado TEXT NOT NULL,

    meet TEXT DEFAULT '',

    fecha_reserva TEXT NOT NULL,

    FOREIGN KEY(disponibilidad_id) REFERENCES disponibilidades(id),

    FOREIGN KEY(alumno_id) REFERENCES users(id)

)
""")

for nombre, definicion in (
    ("profesor_id", "INTEGER DEFAULT 0"),
    ("profesor_nombre", "TEXT DEFAULT ''"),
    ("turno", "TEXT DEFAULT ''"),
    ("meet", "TEXT DEFAULT ''"),
):
    try:
        cursor.execute(f"ALTER TABLE reservas ADD COLUMN {nombre} {definicion}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS asistencias (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reserva_id INTEGER NOT NULL,

    confirmacion_alumno INTEGER DEFAULT 0,

    confirmacion_profesor INTEGER DEFAULT 0,

    fecha_confirmacion TEXT,

    FOREIGN KEY(reserva_id) REFERENCES reservas(id)

)
""")

conn.commit()
conn.close()

print("Base de datos creada")
