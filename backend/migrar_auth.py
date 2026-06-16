import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def agregar_columna(nombre, definicion):
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {nombre} {definicion}")
        print(f"Columna agregada: {nombre}")
    except sqlite3.OperationalError:
        print(f"La columna {nombre} ya existe")

agregar_columna("tokens", "INTEGER DEFAULT 2")
agregar_columna("intentos_fallidos", "INTEGER DEFAULT 0")
agregar_columna("bloqueado", "INTEGER DEFAULT 0")
agregar_columna("rol", "TEXT DEFAULT 'alumno'")

conn.commit()
conn.close()

print("Migración terminada correctamente.")