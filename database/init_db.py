'''
Crear la base de datos SQLite y la tabla de usuarios si no existen.
Este script se ejecuta una sola vez para inicializar la base de datos.
'''

from database.db import get_db ## Importar la función get_db para obtener una conexión a la base de datos

db = get_db()

# Crear tabla
db.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    tokens INTEGER DEFAULT 0
)
""")

db.commit()
db.close()

print("Base de datos creada")