MELANIE FERNANDA PEDROZA INFANTE 
4_D
<img width="184" height="138" alt="9cce55a5-2660-4ca7-b671-4e4d260b5c26" src="https://github.com/user-attachments/assets/683e2c65-b810-481e-ad7c-feec5e1f2227" />

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
