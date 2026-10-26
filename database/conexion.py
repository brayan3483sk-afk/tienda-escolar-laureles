import os
import sys
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv

try:
    from mysql.connector import Error as MySQLError
    import mysql.connector
except ImportError:  # Permite desplegar solo con el driver de PostgreSQL
    MySQLError = Exception
    mysql = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # Permite seguir usando MySQL local sin psycopg2 instalado
    psycopg2 = None
    RealDictCursor = None

# Asegurar codificación utf-8 en consola Windows si es posible
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Cargar variables de entorno desde .env
load_dotenv()

DATABASE_URL = (
    os.getenv('DATABASE_URL')
    or os.getenv('MYSQL_URL')
    or os.getenv('POSTGRES_URL')
    or ''
).strip()
DB_ENGINE = os.getenv('DB_ENGINE', '').strip().lower()


def _load_db_config():
    """Lee la configuración desde DATABASE_URL o desde variables DB_*."""
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        scheme = parsed.scheme.lower()
        is_postgres = scheme.startswith('postgres') or DB_ENGINE == 'postgres'
        query = parse_qs(parsed.query)
        return {
            'engine': 'postgres' if is_postgres else 'mysql',
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or (5432 if is_postgres else 3306),
            'user': unquote(parsed.username or ('postgres' if is_postgres else 'root')),
            'password': unquote(parsed.password or ''),
            'database': (
                (parsed.path or '').lstrip('/')
                or os.getenv('DB_NAME', 'tienda_escolar')
            ),
            'sslmode': os.getenv('DB_SSLMODE') or query.get('sslmode', [None])[0],
        }
    return {
        'engine': 'postgres' if DB_ENGINE == 'postgres' else 'mysql',
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432 if DB_ENGINE == 'postgres' else 3306)),
        'user': os.getenv('DB_USER', 'postgres' if DB_ENGINE == 'postgres' else 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'tienda_escolar'),
        'sslmode': os.getenv('DB_SSLMODE'),
    }


_DB_CONFIG = _load_db_config()
DB_ENGINE = _DB_CONFIG['engine']
IS_POSTGRES = DB_ENGINE == 'postgres'
DB_HOST = _DB_CONFIG['host']
DB_PORT = _DB_CONFIG['port']
DB_USER = _DB_CONFIG['user']
DB_PASSWORD = _DB_CONFIG['password']
DB_NAME = _DB_CONFIG['database']
DB_SSLMODE = _DB_CONFIG['sslmode']

SQL_FILE_MYSQL = 'tienda_escolar.sql'
SQL_FILE_POSTGRES = 'tienda_escolar_postgres.sql'


def get_db_connection(use_database=True):
    """
    Retorna una conexión MySQL o PostgreSQL según DATABASE_URL/DB_ENGINE.
    Compatible con XAMPP local, MySQL remoto y Render Postgres.
    """
    try:
        if IS_POSTGRES:
            if psycopg2 is None:
                print("[ERROR] psycopg2 no está instalado. No se puede conectar a PostgreSQL.")
                return None
            connection_kwargs = {
                'host': DB_HOST,
                'port': DB_PORT,
                'user': DB_USER,
                'password': DB_PASSWORD,
                'connect_timeout': 10,
            }
            if use_database:
                connection_kwargs['dbname'] = DB_NAME
            else:
                connection_kwargs['dbname'] = 'postgres'
            if DB_SSLMODE:
                connection_kwargs['sslmode'] = DB_SSLMODE
            return psycopg2.connect(**connection_kwargs)

        if mysql is None:
            print("[ERROR] mysql-connector-python no está instalado. No se puede conectar a MySQL.")
            return None
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
        return mysql.connector.connect(**connection_kwargs)
    except Exception as e:
        engine = 'PostgreSQL' if IS_POSTGRES else 'MySQL'
        print(f"[ERROR] No se pudo conectar a {engine} en {DB_HOST}:{DB_PORT}. Detalle: {e}")
        return None


def get_dict_cursor(connection):
    """Retorna un cursor que entrega filas tipo diccionario en ambos motores."""
    if IS_POSTGRES:
        return connection.cursor(cursor_factory=RealDictCursor)
    return connection.cursor(dictionary=True)


def execute_query(query, params=None, commit=True):
    """
    Ejecuta consultas de modificación con parámetros (previene SQL Injection).
    En PostgreSQL agrega RETURNING id a los INSERT para poder devolver el ID creado.
    """
    connection = get_db_connection()
    if not connection:
        raise Exception("Servidor de base de datos desconectado. Verifique la conexión.")

    cursor = connection.cursor()
    try:
        if IS_POSTGRES and query.lstrip().upper().startswith('INSERT') and 'RETURNING' not in query.upper():
            cursor.execute(query.rstrip().rstrip(';') + ' RETURNING id', params or ())
            row = cursor.fetchone()
            last_id = row[0] if row else None
        else:
            cursor.execute(query, params or ())
            last_id = getattr(cursor, 'lastrowid', None)

        row_count = cursor.rowcount
        if commit:
            connection.commit()
        return last_id if last_id else row_count
    except Exception as e:
        connection.rollback()
        print(f"[ERROR] Error al ejecutar query SQL: {e}")
        raise e
    finally:
        cursor.close()
        connection.close()


def fetch_all(query, params=None):
    """Ejecuta SELECT y retorna todos los registros como lista de diccionarios."""
    connection = get_db_connection()
    if not connection:
        return []

    cursor = get_dict_cursor(connection)
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[ERROR] Error en fetch_all: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    """Ejecuta SELECT y retorna un único registro como diccionario o None."""
    connection = get_db_connection()
    if not connection:
        return None

    cursor = get_dict_cursor(connection)
    try:
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
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


def _postgres_schema_exists():
    connection = get_db_connection(use_database=True)
    if not connection:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'usuarios'"
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"[WARNING] No se pudo verificar el esquema PostgreSQL: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def _initialize_postgres(sql_filepath):
    if _postgres_schema_exists():
        return True

    print(f"[INFO] Base de datos PostgreSQL '{DB_NAME}' vacía. Ejecutando script SQL...")
    connection = get_db_connection(use_database=True)
    if not connection:
        print("[WARNING] No se pudo conectar a PostgreSQL para inicialización automática.")
        return False

    cursor = connection.cursor()
    try:
        if os.path.exists(sql_filepath):
            with open(sql_filepath, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            cursor.execute(sql_script)
            connection.commit()
            print(f"[SUCCESS] Esquema y datos semilla de PostgreSQL inicializados correctamente.")
            return True
        print(f"[WARNING] No se encontró el script SQL '{sql_filepath}'.")
        return False
    except Exception as e:
        connection.rollback()
        print(f"[WARNING] No se pudo inicializar PostgreSQL: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def _initialize_mysql(sql_filepath):
    db_name = _safe_db_name(DB_NAME)

    # 1. Verificar si la base de datos ya tiene la estructura creada
    conn = get_db_connection(use_database=True)
    if conn:
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
        print("[WARNING] No se pudo conectar a MySQL para inicialización automática. Verifique las credenciales.")
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
        return True
    except Exception as e:
        print(f"[WARNING] No se pudo completar la inicialización automática de MySQL: {e}")
        return False
    finally:
        cursor.close()
        conn_raw.close()


def auto_initialize_db(sql_filepath=None):
    """
    Crea/actualiza la estructura y los datos semilla cuando la tabla principal no existe.
    Funciona con MySQL (XAMPP/remoto) y PostgreSQL (Render).
    Se puede desactivar con AUTO_INIT_DB=false.
    """
    if os.getenv('AUTO_INIT_DB', 'true').strip().lower() in ('0', 'false', 'no', 'off'):
        return True

    try:
        if IS_POSTGRES:
            return _initialize_postgres(sql_filepath or SQL_FILE_POSTGRES)
        return _initialize_mysql(sql_filepath or SQL_FILE_MYSQL)
    except Exception as e:
        print(f"[WARNING] No se pudo completar la inicialización automática de BD: {e}")
        return False
