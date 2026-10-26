import re
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario import Usuario
from extensions import limiter

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta sección.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Acceso no autorizado. Inicie sesión.', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('rol') != 'Administrador':
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('menu.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if 'user_id' in session:
        if session.get('rol') == 'Administrador':
            return redirect(url_for('inventario.dashboard'))
        return redirect(url_for('menu.index'))

    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()

        if not username or not password:
            flash('Ingrese el usuario y la contraseña.', 'danger')
            return render_template('login.html')

        user = Usuario.get_by_usuario(username)
        if not user or user['estado'] != 'Activo':
            flash('Usuario no encontrado o inactivo.', 'danger')
            return render_template('login.html')

        if Usuario.verificar_contrasena(user['contrasena'], password):
            session['user_id'] = user['id']
            session['nombre'] = user['nombre']
            session['usuario'] = user['usuario']
            session['rol'] = user['rol']
            session['carrito'] = []

            flash(f'¡Bienvenido(a), {user["nombre"]}!', 'success')
            if user['rol'] == 'Administrador':
                return redirect(url_for('inventario.dashboard'))
            return redirect(url_for('menu.index'))
        else:
            flash('Contraseña incorrecta. Intente nuevamente.', 'danger')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if 'user_id' in session:
        return redirect(url_for('menu.index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '').strip()

        if not nombre or not username or not password:
            flash('Por favor completa todos los campos.', 'danger')
            return render_template('register.html')
            
        # Validación estricta de seguridad
        if not re.match(r"^[a-zA-Z0-9_.-]{4,20}$", username):
            flash('El usuario debe tener entre 4 y 20 caracteres y sin espacios.', 'danger')
            return render_template('register.html')
            
        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[a-zA-Z]", password):
            flash('La contraseña debe tener al menos 8 caracteres, incluyendo letras y números.', 'danger')
            return render_template('register.html')

        # Verificar si el usuario ya existe
        user_existente = Usuario.get_by_usuario(username)
        if user_existente:
            flash('Este nombre de usuario ya está en uso. Elige otro.', 'warning')
            return render_template('register.html')

        # Crear usuario (por defecto rol Estudiante)
        exito = Usuario.crear_usuario(nombre, username, password, rol='Estudiante')
        if exito:
            flash('Cuenta creada con éxito. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Hubo un error al crear la cuenta. Inténtalo de nuevo.', 'danger')

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Ha cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.get_all_usuarios()
    return render_template('admin_usuarios.html', usuarios=usuarios)

@auth_bp.route('/admin/usuarios/cambiar_rol', methods=['POST'])
@admin_required
def cambiar_rol_usuario():
    user_id = request.form.get('user_id', type=int)
    nuevo_rol = request.form.get('nuevo_rol')

    if user_id == session.get('user_id'):
        flash('No puedes cambiar tu propio rol por seguridad.', 'warning')
        return redirect(url_for('auth.admin_usuarios'))

    if user_id == 1:
        flash('Acción denegada: No se pueden modificar los permisos del Super Usuario (Administrador principal).', 'danger')
        return redirect(url_for('auth.admin_usuarios'))

    if nuevo_rol not in ['Administrador', 'Estudiante']:
        flash('Rol no válido.', 'danger')
        return redirect(url_for('auth.admin_usuarios'))

    exito = Usuario.cambiar_rol(user_id, nuevo_rol)
    if exito:
        flash(f'El rol del usuario ha sido actualizado a {nuevo_rol}.', 'success')
    else:
        flash('Hubo un error al actualizar el rol.', 'danger')

    return redirect(url_for('auth.admin_usuarios'))
