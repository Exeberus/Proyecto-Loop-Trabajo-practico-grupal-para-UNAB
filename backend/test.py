import sqlite3
import os

print("CARPETA SCRIPT:", os.getcwd())
print("RUTA DB:", os.path.abspath("database.db"))

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
SELECT name FROM sqlite_master
WHERE type='table'
""")

print(cursor.fetchall())