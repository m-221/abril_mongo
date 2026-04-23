from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from werkzeug.security import generate_password_hash, check_password_hash


class GestorTareas:
    def __init__(self, uri: str = 'mongodb://localhost:27017/'):
        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')
            self.db = self.cliente['gestor_tareas']
            self.tareas = self.db['tareas']
            self.usuarios = self.db['usuarios']

            self._crear_indices()
            print("✅ Conectado a MongoDB")
        except ConnectionFailure:
            print("❌ Error: No se pudo conectar a MongoDB")
            raise

    def _crear_indices(self):
        self.usuarios.create_index("email", unique=True)
        self.usuarios.create_index("nombre", unique=True)
        self.tareas.create_index([("usuario_id", 1), ("fecha_creacion", -1)])
        self.tareas.create_index("estado")

    # 🔹 CREAR USUARIO
    def crear_usuario(self, nombre: str, email: str, password: str) -> Optional[str]:
        try:
            resultado = self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": generate_password_hash(password),
                "fecha_registro": datetime.now(),
                "activo": True
            })
            return str(resultado.inserted_id)
        except DuplicateKeyError:
            print("❌ Usuario o email ya existe")
            return None

    # 🔹 LOGIN POR NOMBRE
    def iniciar_sesion(self, nombre: str, password: str) -> Optional[Dict]:
        usuario = self.usuarios.find_one({"nombre": nombre})

        if not usuario:
            print("❌ Usuario no existe")
            return None

        if not check_password_hash(usuario["password"], password):
            print("❌ Contraseña incorrecta")
            return None

        if not usuario.get("activo", True):
            print("❌ Usuario inactivo")
            return None

        usuario['_id'] = str(usuario['_id'])
        print("✅ Login exitoso")
        return usuario

    # 🔹 OBTENER USUARIO
    def obtener_usuario(self, usuario_id: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"_id": ObjectId(usuario_id)})
            if usuario:
                usuario['_id'] = str(usuario['_id'])
            return usuario
        except:
            return None

    # 🔹 CREAR TAREA
    def crear_tarea(self, usuario_id: str, titulo: str, descripcion: str = "", fecha_limite: Optional[datetime] = None) -> Optional[str]:
        if not self.obtener_usuario(usuario_id):
            print("❌ Usuario no existe")
            return None

        tarea = {
            "usuario_id": ObjectId(usuario_id),
            "titulo": titulo,
            "descripcion": descripcion,
            "estado": "pendiente",
            "fecha_creacion": datetime.now(),
            "fecha_limite": fecha_limite or datetime.now() + timedelta(days=7),
            "completada": False,
            "etiquetas": []
        }

        resultado = self.tareas.insert_one(tarea)
        return str(resultado.inserted_id)

    # 🔹 OBTENER TAREAS
    def obtener_tareas_usuario(self, usuario_id: str) -> List[Dict]:
        tareas = self.tareas.find({"usuario_id": ObjectId(usuario_id)})
        resultado = []

        for t in tareas:
            t['_id'] = str(t['_id'])
            t['usuario_id'] = str(t['usuario_id'])
            resultado.append(t)

        return resultado

    # 🔹 ACTUALIZAR ESTADO
    def actualizar_estado_tarea(self, tarea_id: str, nuevo_estado: str) -> bool:
        resultado = self.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {"estado": nuevo_estado}}
        )
        return resultado.modified_count > 0

    # 🔹 ELIMINAR TAREA
    def eliminar_tarea(self, tarea_id: str) -> bool:
        resultado = self.tareas.delete_one({"_id": ObjectId(tarea_id)})
        return resultado.deleted_count > 0

    # 🔹 CERRAR
    def cerrar_conexion(self):
        self.cliente.close()
        print("🔌 Conexión cerrada")


# 🔥 EJEMPLO COMPLETO
def ejemplo_uso():
    gestor = GestorTareas()

    # Crear usuario
    usuario_id = gestor.crear_usuario("mely", "mely@email.com", "1234")

    # Login
    usuario = gestor.iniciar_sesion("mely", "1234")

    if usuario:
        print("Bienvenido:", usuario["nombre"])

        # Crear tarea
        tarea_id = gestor.crear_tarea(usuario["_id"], "Estudiar MongoDB")

        # Ver tareas
        tareas = gestor.obtener_tareas_usuario(usuario["_id"])
        print("Tareas:", tareas)

    gestor.cerrar_conexion()


if __name__ == "__main__":
    ejemplo_uso()
