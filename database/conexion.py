import os
import sys
from urllib.parse import unquote, urlparse

from mysql.connector import Error
import mysql.connector
from dotenv import load_dotenv

# Asegurar codificación utf-8 en consola Windows si es posible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Cargar variables de entorno desde .env
load_dotenv()

DATABASE_URL = (os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL') or '').strip()


def _load_db_config():
    """Lee la configuración desde DATABASE_URL/MYSQL_URL o desde variables DB_*."""
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': unquote(parsed.username or 'root'),
            'password': unquote(parsed.password or ''),
            'database': (parsed.path or '').lstrip('/') or os.getenv('DB_NAME', 'tienda_escolar'),
        }
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'tienda_escolar'),
    }


_DB_CONFIG = _load_db_config()
DB_HOST = _DB_CONFIG['host']
DB_PORT = _DB_CONFIG['port']
DB_USER = _DB_CONFIG['user']
DB_PASSWORD = _DB_CONFIG['password']
DB_NAME = _DB_CONFIG['database']


def get_db_connection(use_database=True):
    """
    Establece y retorna una conexión a la base de datos MySQL mediante mysql-connector-python.
    Lee los parámetros desde .env/DATABASE_URL para compatibilidad con Local, Ngrok y Render.
    """
    try:
        connection_kwargs = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'autocommit': False,
            'connection_timeout': 10,
        }
        if use_database:
            connection_kwargs['database'] = DB_NAME

        if os.getenv('DB_SSL', '').strip().lower() in ('0', 'false', 'no', 'disabled'):
            connection_kwargs['ssl_disabled'] = True

        connection = mysql.connector.connect(**connection_kwargs)
        return connection
    except Error as e:
        print(f"[ERROR] No se pudo conectar a la base de datos MySQL en {DB_HOST}:{DB_PORT}. (Asegurese de iniciar el servicio MySQL en XAMPP). Detalle: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error inesperado en conexión MySQL: {e}")
        return None


def execute_query(query, params=None, commit=True):
    """
    Ejecuta consultas de modificación (INSERT, UPDATE, DELETE) con consultas parametrizadas
    para evitar vulnerabilidades de SQL Injection.
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Servidor MySQL desconectado. Inicie XAMPP e intente de nuevo.")
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        last_id = cursor.lastrowid
        row_count = cursor.rowcount
        if commit:
            connection.commit()
        return last_id if last_id else row_count
    except Error as e:
        connection.rollback()
        print(f"[ERROR] Error al ejecutar query SQL: {e}")
        raise e
    finally:
        cursor.close()
        connection.close()


def fetch_all(query, params=None):
    """
    Ejecuta consultas SELECT y retorna todos los registros como una lista de diccionarios.
    """
    connection = get_db_connection()
    if not connection:
        return []
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"[ERROR] Error en fetch_all: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    """
    Ejecuta consultas SELECT y retorna un único registro como diccionario o None.
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"[ERROR] Error en fetch_one: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def _safe_db_name(name):
    """Evita inyección SQL al interpolar el nombre de la base de datos."""
    cleaned = ''.join(ch for ch in (name or '') if ch.isalnum() or ch == '_')
    return cleaned or 'tienda_escolar'


def _strip_sql_comments(statement):
    lines = [line for line in statement.splitlines() if not line.strip().startswith('--')]
    return '\n'.join(lines).strip()


def auto_initialize_db(sql_filepath="tienda_escolar.sql"):
    """
    Crea la base de datos (si el usuario tiene permisos) y ejecuta el script SQL cuando
    la tabla principal no existe. Funciona tanto en XAMPP local como en MySQL remoto.
    Se puede desactivar con AUTO_INIT_DB=false.
    """
    if os.getenv('AUTO_INIT_DB', 'true').strip().lower() in ('0', 'false', 'no', 'off'):
        return True

    db_name = _safe_db_name(DB_NAME)

    try:
        # 1. Verificar si la base de datos ya tiene la estructura creada
        conn = get_db_connection(use_database=True)
        if conn and conn.is_connected():
            cursor = conn.cursor()
            try:
                cursor.execute("SHOW TABLES LIKE 'usuarios'")
                if cursor.fetchone():
                    return True
            finally:
                cursor.close()
                conn.close()
            print(f"[INFO] Base de datos '{db_name}' existe pero está vacía. Ejecutando script SQL...")
        else:
            print(f"[INFO] Base de datos '{db_name}' no disponible. Intentando inicialización automática...")

        # 2. Conectar sin base de datos y crear/ejecutar la estructura
        conn_raw = get_db_connection(use_database=False)
        if not conn_raw:
            print("[WARNING] No se pudo conectar a MySQL para inicialización automática. Verifique las credenciales del servidor.")
            return False

        cursor = conn_raw.cursor()
        try:
            try:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            except Exception as e:
                print(f"[WARNING] No se pudo crear la base de datos '{db_name}' (puede que ya exista o falten permisos): {e}")

            cursor.execute(f"USE `{db_name}`")

            if os.path.exists(sql_filepath):
                with open(sql_filepath, 'r', encoding='utf-8') as f:
                    sql_script = f.read()

                statements = [_strip_sql_comments(s) for s in sql_script.split(';')]
                for statement in statements:
                    if not statement:
                        continue
                    upper = statement.upper()
                    if upper.startswith('CREATE DATABASE') or upper.startswith('USE '):
                        continue
                    cursor.execute(statement)

                conn_raw.commit()
                print(f"[SUCCESS] Base de datos '{db_name}' y datos semilla inicializados correctamente.")
            else:
                print(f"[WARNING] No se encontró el script SQL '{sql_filepath}'.")
        finally:
            cursor.close()
            conn_raw.close()
        return True
    except Exception as e:
        print(f"[WARNING] No se pudo completar la inicialización automática de BD: {e}")
        return False
