import sqlite3
import os

print("CARPETA ACTUAL:")
print(os.getcwd())

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
               
    id INTEGER PRIMARY KEY AUTOINCREMENT,
               
    username TEXT NOT NULL UNIQUE,
               
    email TEXT NOT NULL UNIQUE,
               
    password TEXT NOT NULL
    
)
"""
)

cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    reviewer_id INTEGER NOT NULL,

    rated_user_id INTEGER NOT NULL,

    stars INTEGER NOT NULL,

    FOREIGN KEY(reviewer_id) REFERENCES users(id),
    FOREIGN KEY(rated_user_id) REFERENCES users(id)

)
""")

conn.commit()
conn.close()

print("Base de datos creada")