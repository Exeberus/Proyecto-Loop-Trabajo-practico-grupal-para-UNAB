'''
Blueprint en Flask sirve para:

separar el código
organizar rutas
evitar que todo esté en app.py
'''

from flask import Blueprint, jsonify ## Importar Blueprint para crear un grupo de rutas y jsonify para convertir datos a JSON
from database.db import get_db ## Importar la función get_db para obtener una conexión a la base de datos

users_bp = Blueprint("users", __name__)

@users_bp.route("/api/users/<int:user_id>", methods=["GET"]) ## Definir una ruta para obtener un usuario específico
def get_user(user_id): ## Función para manejar la solicitud GET a /api/users/<id>
    db = get_db()

    users = db.execute(
        "SELECT * FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    
    db.close()

    if users is None:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    return jsonify(dict(users))