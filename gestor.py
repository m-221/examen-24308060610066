from flask import Flask
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

import smtplib
from email.mime.text import MIMEText
import random
from main import EMAIL_USER, EMAIL_PASS


app = Flask(__name__)



def enviar_correo(destinatario, codigo):
    mensaje = MIMEText(f"Tu código es: {codigo}")
    mensaje['Subject'] = "Código"
    mensaje['From'] = EMAIL_USER
    mensaje['To'] = destinatario

    try:
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.set_debuglevel(1)
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()

        servidor.login(EMAIL_USER, EMAIL_PASS)

        resultado = servidor.sendmail(
            EMAIL_USER,
            destinatario,
            mensaje.as_string()
        )

        servidor.quit()

        print("Resultado envío:", resultado)

        if resultado == {}:
            print("✅ Correo enviado correctamente")
            return True   
        else:
            print("⚠️ Algo falló:", resultado)
            return False 

    except Exception as e:
        print("❌ Error enviando correo:", e)
        return False 


class GestorTareas:
    def __init__(self):
        try:
            self.cliente = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')

            self.db = self.cliente['gestor_tareas']
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
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError:
            return None

    def crear_usuario(self, nombre, email, password):
        email_valido = self.validar_email(email)

        if not email_valido:
            return None, "Correo inválido"

        if not nombre or not password:
            return None, "Faltan datos"

        try:
            codigo = str(random.randint(100000, 999999))

        
            enviar_correo(email_valido, codigo)

            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email_valido,
                "password": generate_password_hash(password),
                "fecha": datetime.now(),
                "activo": False,
                "codigo": codigo
            })

            return str(resultado.inserted_id), None

        except DuplicateKeyError:
            return None, "El correo o usuario ya existe"

       
        except Exception as e:
            print("❌ Error general:", e)
            return None, "Error al registrar usuario"


gestor = GestorTareas()


if __name__ == '__main__':
    app.run(debug=True)