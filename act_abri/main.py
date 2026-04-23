from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta"

client = MongoClient("mongodb://localhost:27017/")
db = client["mi_base"]
usuarios = db["usuarios"]



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
            session['username'] = username
            session['user_id'] = str(usuario["_id"])
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('gestordetareas'))
        else:
            flash('Credenciales incorrectas', 'danger')

    return render_template('inicioseccion.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form.get('nombre')
        password = request.form.get('password')


        if usuarios.find_one({"nombre": username}):
            flash('El usuario ya existe', 'danger')
            return redirect(url_for('registro'))

        
        usuarios.insert_one({
            "nombre": username,
            "password": generate_password_hash(password)
        })

        flash('Registro exitoso', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')



@app.route('/gestordetarea')
def gestordetareas():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('gestordetarea.html', usuario=session['username'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)