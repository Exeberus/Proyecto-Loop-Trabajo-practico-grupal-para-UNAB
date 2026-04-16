'''
Crear conexión a la base de datos SQLite y configurar el cursor para que devuelva filas como diccionarios.
'''
import sqlite3 ## Importar el módulo sqlite3 para trabajar con bases de datos SQLite

def get_db(): ## Función para obtener una conexión a la base de datos
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn