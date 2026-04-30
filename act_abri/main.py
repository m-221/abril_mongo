from flask import Flask, render_template, request, redirect, session, url_for, flash 
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

import random
from datetime import datetime
from bson.objectid import ObjectId

from config import SECRET_KEY, MONGO_URI, DB_NAME
from gestor import enviar_correo   

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
usuarios = db["usuarios"]
tareas = db["tareas"]  

try:
    usuarios.drop_index("email_1")
except Exception:
    pass

usuarios.create_index("email", unique=True, sparse=True)


@app.route('/')
def base():
    return render_template('base.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        usuario = usuarios.find_one({"nombre": username})

        if usuario and check_password_hash(usuario["password"], password):

            if not usuario.get("activo"):
                flash("Debes verificar tu correo", "warning")
                return redirect(url_for('login'))

            session['username'] = username
            session['user_id'] = str(usuario["_id"])

            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('gestordetareas'))

        flash('Credenciales incorrectas', 'danger')

    return render_template('inicioseccion.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':

        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmar = request.form.get('confirmar')

        if not nombre or not email or not password or not confirmar:
            return render_template('registro.html', error="Todos los campos son obligatorios")

        if password != confirmar:
            return render_template('registro.html', error="Las contraseñas no coinciden")

        try:
            valid = validate_email(email)
            email_valido = valid.email
        except EmailNotValidError:
            return render_template('registro.html', error="Correo inválido")

        try:
            codigo = str(random.randint(100000, 999999))

            enviar_correo(email_valido, codigo)

            usuarios.insert_one({
                "nombre": nombre,
                "email": email_valido,
                "password": generate_password_hash(password),
                "activo": False,
                "codigo": codigo,
                "fecha": datetime.now()
            })

            flash("Revisa tu correo para verificar tu cuenta", "success")
            return redirect(url_for('verificar'))

        except DuplicateKeyError:
            return render_template('registro.html', error="El usuario o correo ya existe")

    return render_template('registro.html')


@app.route('/verificar', methods=['GET', 'POST'])
def verificar():
    if request.method == 'POST':
        codigo = request.form.get('codigo')

        usuario = usuarios.find_one({"codigo": codigo})

        if usuario:
            usuarios.update_one(
                {"_id": usuario["_id"]},
                {"$set": {"activo": True}, "$unset": {"codigo": ""}}
            )

            flash("Cuenta verificada correctamente", "success")
            return redirect(url_for('login'))

        flash("Código incorrecto", "danger")

    return render_template('verificar.html')


@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        email = request.form.get('email')

        usuario = usuarios.find_one({"email": email})

        if usuario:
            codigo = str(random.randint(100000, 999999))

            usuarios.update_one(
                {"_id": usuario["_id"]},
                {"$set": {"codigo_recuperacion": codigo}}
            )

            enviar_correo(email, codigo)

            return redirect(url_for('resetear'))

        flash("Correo no encontrado", "danger")

    return render_template('recuperar.html')


@app.route('/resetear', methods=['GET', 'POST'])
def resetear():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nueva = request.form.get('password')
        confirmar = request.form.get('confirmar')

        if nueva != confirmar:
            flash("Las contraseñas no coinciden", "danger")
            return redirect(url_for('resetear'))

        usuario = usuarios.find_one({"codigo_recuperacion": codigo})

        if usuario:
            usuarios.update_one(
                {"_id": usuario["_id"]},
                {
                    "$set": {"password": generate_password_hash(nueva)},
                    "$unset": {"codigo_recuperacion": ""}
                }
            )

            flash("Contraseña actualizada", "success")
            return redirect(url_for('login'))

        flash("Código inválido", "danger")

    return render_template('resetear.html')


@app.route('/gestordetarea')
def gestordetareas():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('gestordetarea.html', usuario=session['username'])


@app.route('/gestorsecundario')
def gestorsecundario():
    if 'username' not in session:
        return redirect(url_for('login'))

    tareas_usuario = tareas.find({"usuario": session['username']})

    return render_template(
        'gestorsecundario.html',
        usuario=session['username'],
        tareas=tareas_usuario


    )



@app.route('/agregartarea', methods=['GET', 'POST'])
def agregartarea():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')

        tareas.insert_one({
            "nombre": nombre,
            "descripcion": descripcion,
            "usuario": session['username'],
            "estado": "pendiente"
        })

        return redirect(url_for('gestorsecundario'))

    return render_template('agregar.html')

@app.route('/completar/<id>')
def completar(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    from bson.objectid import ObjectId

    tareas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "completada"}}
    )

    return redirect(url_for('gestorsecundario'))


@app.route('/borrar/<id>')
def borrar(id):
    tareas.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('gestorsecundario'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)