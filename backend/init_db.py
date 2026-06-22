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

conn.commit()
conn.close()

print("Base de datos creada")
