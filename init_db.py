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
"""
)

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