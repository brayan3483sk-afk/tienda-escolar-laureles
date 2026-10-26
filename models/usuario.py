from werkzeug.security import generate_password_hash, check_password_hash
from database.conexion import fetch_one, fetch_all, execute_query

class Usuario:
    @staticmethod
    def get_by_usuario(usuario_str):
        query = "SELECT * FROM usuarios WHERE usuario = %s"
        return fetch_one(query, (usuario_str,))

    @staticmethod
    def get_by_id(user_id):
        query = "SELECT * FROM usuarios WHERE id = %s"
        return fetch_one(query, (user_id,))

    @staticmethod
    def get_all_usuarios():
        query = "SELECT id, nombre, usuario, rol, estado FROM usuarios ORDER BY id ASC"
        return fetch_all(query)

    @staticmethod
    def crear_usuario(nombre, usuario_str, contrasena_raw, rol='Estudiante'):
        hash_password = generate_password_hash(contrasena_raw)
        query = """
            INSERT INTO usuarios (nombre, usuario, contrasena, rol, estado)
            VALUES (%s, %s, %s, %s, 'Activo')
        """
        return execute_query(query, (nombre, usuario_str, hash_password, rol))

    @staticmethod
    def actualizar_usuario(user_id, nombre, usuario_str, rol=None, estado=None):
        if rol and estado:
            query = "UPDATE usuarios SET nombre = %s, usuario = %s, rol = %s, estado = %s WHERE id = %s"
            return execute_query(query, (nombre, usuario_str, rol, estado, user_id))
        else:
            query = "UPDATE usuarios SET nombre = %s, usuario = %s WHERE id = %s"
            return execute_query(query, (nombre, usuario_str, user_id))

    @staticmethod
    def cambiar_contrasena(user_id, nueva_contrasena_raw):
        hash_password = generate_password_hash(nueva_contrasena_raw)
        query = "UPDATE usuarios SET contrasena = %s WHERE id = %s"
        return execute_query(query, (hash_password, user_id))

    @staticmethod
    def eliminar_logico(user_id):
        """Borrado lógico (Soft Delete) cambiando el estado a Inactivo"""
        query = "UPDATE usuarios SET estado = 'Inactivo' WHERE id = %s"
        return execute_query(query, (user_id,))

    @staticmethod
    def reactivar(user_id):
        query = "UPDATE usuarios SET estado = 'Activo' WHERE id = %s"
        return execute_query(query, (user_id,))

    @staticmethod
    def cambiar_rol(user_id, nuevo_rol):
        query = "UPDATE usuarios SET rol = %s WHERE id = %s"
        return execute_query(query, (nuevo_rol, user_id))

    @staticmethod
    def verificar_contrasena(hash_almacenado, contrasena_raw):
        return check_password_hash(hash_almacenado, contrasena_raw)
