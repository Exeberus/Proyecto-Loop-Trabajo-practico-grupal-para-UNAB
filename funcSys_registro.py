## Funciones para Register
## Validar registro
def validarRegistro():

    if len(username) < 3:
        error = "El usuario debe tener al menos 3 caracteres"
    
    elif len (password) < 6:
        error = "La contraseña debe tener al menos 6 caracteres"

    elif " " in username:
        error = "El usuario no puede tener espacios"

    else:
        return "Usuario válido"
    return render_template("register.html", error=error)