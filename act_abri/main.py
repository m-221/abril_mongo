from flask import Flask, render_template, request, redirect, session, url_for, flash

app = Flask(__name__)
app.secret_key = "clave_secreta"  


@app.route('/')
def base():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    usuarios = {
        "admin": "password",
        "mely": "1234"
    }

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in usuarios and usuarios[username] == password:
            session['username'] = username
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('gestor'))
        else:
            flash('Credenciales incorrectas', 'danger')

    return render_template('inicioseccion.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        flash('Registro exitoso', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')



if __name__ == '__main__':
    app.run(debug=True)