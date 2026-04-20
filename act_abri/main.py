from flask import Flask, render_template, request, redirect, session, url_for, flash

app = Flask(__name__)
app.secret_key = "clave_secreta"  

usuarios = {
    "mely": "1234"
}


@app.route('/')
def base():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in usuarios and usuarios[username] == password:
            session['username'] = username
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
        usuarios[username] = password
        flash('Registro exitoso', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/gestordetarea')
def gestordetareas():
    return render_template('gestordetarea.html')



if __name__ == '__main__':
    app.run(debug=True)