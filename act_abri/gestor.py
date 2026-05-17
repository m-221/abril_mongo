from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure

from datetime import datetime
from werkzeug.security import generate_password_hash

from email_validator import (
    validate_email,
    EmailNotValidError
)

import smtplib
from email.mime.text import MIMEText

import random
import secrets

from config import (
    EMAIL_USER,
    EMAIL_PASS,
    MONGO_URI,
    DB_NAME
)




def enviar_correo(destinatario, codigo):

    mensaje = MIMEText(f"""
    <html>
    <body>

        <h2>Verificación de cuenta</h2>

        <p>
            Hola,
        </p>

        <p>
            Gracias por registrarte en
            <b>Gestor de Tareas</b>.
        </p>

        <p>
            Tu código de verificación es:
        </p>

        <h1>{codigo}</h1>

        <p>
            No compartas este código con nadie.
        </p>

        <p>
            Equipo de Gestor de Tareas
        </p>

    </body>
    </html>
    """, "html")

    mensaje['Subject'] = "Verificación de cuenta"
    mensaje['From'] = EMAIL_USER
    mensaje['To'] = destinatario

    try:

        servidor = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        servidor.starttls()

        servidor.login(
            EMAIL_USER,
            EMAIL_PASS
        )

        servidor.sendmail(
            EMAIL_USER,
            destinatario,
            mensaje.as_string()
        )

        servidor.quit()

        print("✅ Correo enviado")

        return True

    except Exception as e:

        print("❌ Error correo:", e)

        return False




def enviar_correo_recuperacion(destinatario, link):

    mensaje = MIMEText(f"""
    <html>
    <body>

        <h2>Recuperación de contraseña</h2>

        <p>
            Hola,
        </p>

        <p>
            Recibimos una solicitud para
            restablecer tu contraseña.
        </p>

        <p>
            Haz clic en el siguiente enlace:
        </p>

        <p>
            <a href="{link}">
                Restablecer contraseña
            </a>
        </p>

        <p>
            Si no realizaste esta solicitud,
            puedes ignorar este mensaje.
        </p>

        <p>
            Equipo de Gestor de Tareas
        </p>

    </body>
    </html>
    """, "html")

    mensaje['Subject'] = "Recuperación de contraseña"
    mensaje['From'] = EMAIL_USER
    mensaje['To'] = destinatario

    try:

        servidor = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        servidor.starttls()

        servidor.login(
            EMAIL_USER,
            EMAIL_PASS
        )

        servidor.sendmail(
            EMAIL_USER,
            destinatario,
            mensaje.as_string()
        )

        servidor.quit()

        print("✅ Correo recuperación enviado")

        return True

    except Exception as e:

        print("❌ Error recuperación:", e)

        return False




class GestorTareas:

    def __init__(self):

        try:

            self.cliente = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000
            )

            self.cliente.admin.command('ping')

            self.db = self.cliente[DB_NAME]

            self.usuarios = self.db['usuarios']

            self.usuarios.create_index(
                "email",
                unique=True,
                sparse=True
            )

            print("✅ Mongo conectado")

        except ConnectionFailure:

            print("❌ Error Mongo")

            raise


   

    def validar_email(self, email):

        try:

            valid = validate_email(
                email,
                check_deliverability=False
            )

            return valid.email

        except EmailNotValidError:

            return None


    

    def crear_usuario(
        self,
        nombre,
        email,
        password
    ):

        email_valido = self.validar_email(email)

        if not email_valido:

            return None, "Correo inválido"

        if not nombre or not password:

            return None, "Faltan datos"

        try:

            codigo = str(
                random.randint(100000, 999999)
            )

            if not enviar_correo(
                email_valido,
                codigo
            ):

                return None, (
                    "No se pudo enviar el correo"
                )

            resultado = self.usuarios.insert_one({

                "nombre": nombre,

                "email": email_valido,

                "password": generate_password_hash(
                    password
                ),

                "fecha": datetime.now(),

                "activo": False,

                "codigo": codigo

            })

            return (
                str(resultado.inserted_id),
                None
            )

        except DuplicateKeyError:

            return None, (
                "El correo ya existe"
            )

        except Exception as e:

            print("❌ Error:", e)

            return None, (
                "Error al registrar usuario"
            )


    

    def generar_token_recuperacion(
        self,
        email
    ):

        usuario = self.usuarios.find_one({
            "email": email
        })

        if not usuario:

            return None

        token = secrets.token_urlsafe(32)

        self.usuarios.update_one(

            {"_id": usuario["_id"]},

            {
                "$set": {
                    "token_recuperacion": token
                }
            }
        )

        return token


  

    def resetear_password(
        self,
        token,
        nueva_password
    ):

        usuario = self.usuarios.find_one({

            "token_recuperacion": token

        })

        if not usuario:

            return False

        self.usuarios.update_one(

            {"_id": usuario["_id"]},

            {

                "$set": {

                    "password":
                    generate_password_hash(
                        nueva_password
                    )

                },

                "$unset": {

                    "token_recuperacion": ""

                }

            }

        )

        return True





gestor = GestorTareas()