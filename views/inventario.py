import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from views.auth import admin_required
from models.producto import Producto
from models.pedido import Pedido
from models.usuario import Usuario

inventario_bp = Blueprint('inventario', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def validate_image_header(file_stream):
    """
    Lee los primeros bytes del archivo (Magic Bytes) para confirmar que realmente
    sea una imagen válida y prevenir subidas de web shells o malware ofuscado.
    """
    header = file_stream.read(12)
    file_stream.seek(0) # Regresar el cursor al inicio para que save() funcione
    
    if header.startswith(b'\xff\xd8\xff'):
        return True # JPEG
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return True # PNG
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return True # GIF
    elif header[0:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True # WEBP
        
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@inventario_bp.route('/dashboard')
@admin_required
def dashboard():
    # Obtener métricas rápidas para el dashboard
    productos = Producto.get_all_productos(solo_activos=False)
    pedidos_pendientes = Pedido.get_all_pedidos(filtro_estado='PENDIENTE')
    todos_pedidos = Pedido.get_all_pedidos()
    
    total_ventas = sum(p['total'] for p in todos_pedidos if p['estado'] == 'ENTREGADO')
    stock_bajo = [p for p in productos if p['estado'] == 'Activo' and p['cantidad'] <= 5]
    
    return render_template(
        'dashboard.html',
        total_productos=len([p for p in productos if p['estado'] == 'Activo']),
        pedidos_pendientes=len(pedidos_pendientes),
        total_pedidos=len(todos_pedidos),
        total_ventas=total_ventas,
        stock_bajo=stock_bajo,
        ultimos_pedidos=todos_pedidos[:5]
    )

@inventario_bp.route('/admin/inventario')
@admin_required
def gestion_inventario():
    productos = Producto.get_all_productos(solo_activos=False)
    categorias = Producto.get_categorias()
    movimientos = Producto.get_movimientos_inventario()
    return render_template('inventario.html', productos=productos, categorias=categorias, movimientos=movimientos)

@inventario_bp.route('/admin/producto/nuevo', methods=['POST'])
@admin_required
def nuevo_producto():
    nombre = request.form.get('nombre', '').strip()
    id_categoria = request.form.get('id_categoria', type=int)
    precio = request.form.get('precio', type=float)
    cantidad = request.form.get('cantidad', type=int, default=0)

    if not nombre or not id_categoria or precio is None or precio < 0:
        flash('Por favor complete todos los campos obligatorios del producto.', 'danger')
        return redirect(url_for('inventario.gestion_inventario'))

    imagen_filename = 'default_product.png'
    file = request.files.get('imagen')
    if file and file.filename != '':
        if allowed_file(file.filename) and validate_image_header(file.stream):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'productos')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            imagen_filename = filename
        else:
            flash('Error: El archivo subido no es una imagen permitida o su contenido es inválido.', 'danger')
            return redirect(url_for('inventario.gestion_inventario'))

    prod_id = Producto.crear_producto(id_categoria, nombre, precio, cantidad, imagen_filename)
    if prod_id:
        flash(f'¡Producto "{nombre}" creado exitosamente!', 'success')
    else:
        flash('Error al guardar el producto en la base de datos.', 'danger')

    return redirect(url_for('inventario.gestion_inventario'))

@inventario_bp.route('/admin/producto/editar', methods=['POST'])
@admin_required
def editar_producto():
    prod_id = request.form.get('id', type=int)
    nombre = request.form.get('nombre', '').strip()
    id_categoria = request.form.get('id_categoria', type=int)
    precio = request.form.get('precio', type=float)
    cantidad = request.form.get('cantidad', type=int)

    if not prod_id or not nombre or not id_categoria or precio is None:
        flash('Datos inválidos para actualizar el producto.', 'danger')
        return redirect(url_for('inventario.gestion_inventario'))

    imagen_filename = None
    file = request.files.get('imagen')
    if file and file.filename != '':
        if allowed_file(file.filename) and validate_image_header(file.stream):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'productos')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            imagen_filename = filename
        else:
            flash('Error: El archivo subido no es una imagen permitida o su contenido es inválido.', 'danger')
            return redirect(url_for('inventario.gestion_inventario'))

    exito = Producto.actualizar_producto(prod_id, id_categoria, nombre, precio, cantidad, imagen_filename)
    if exito:
        flash(f'¡Producto "{nombre}" actualizado!', 'success')
    else:
        flash('Error al actualizar el producto.', 'danger')

    return redirect(url_for('inventario.gestion_inventario'))

@inventario_bp.route('/admin/producto/eliminar/<int:prod_id>', methods=['POST'])
@admin_required
def eliminar_producto(prod_id):
    """Borrado Lógico (Soft Delete)"""
    exito = Producto.eliminar_logico(prod_id)
    if exito:
        flash('Producto desactivado correctamente (Borrado Lógico).', 'info')
    else:
        flash('No se pudo desactivar el producto.', 'danger')
    return redirect(url_for('inventario.gestion_inventario'))

@inventario_bp.route('/admin/producto/reactivar/<int:prod_id>', methods=['POST'])
@admin_required
def reactivar_producto(prod_id):
    exito = Producto.reactivar(prod_id)
    if exito:
        flash('Producto reactivado correctamente.', 'success')
    else:
        flash('No se pudo reactivar el producto.', 'danger')
    return redirect(url_for('inventario.gestion_inventario'))

@inventario_bp.route('/admin/inventario/ajuste', methods=['POST'])
@admin_required
def ajuste_stock():
    prod_id = request.form.get('id_producto', type=int)
    cantidad = request.form.get('cantidad', type=int)
    tipo_mov = request.form.get('tipo_movimiento')
    descripcion = request.form.get('descripcion', '').strip()

    if not prod_id or not cantidad or tipo_mov not in ['ENTRADA', 'SALIDA', 'AJUSTE']:
        flash('Datos de ajuste no válidos.', 'danger')
        return redirect(url_for('inventario.gestion_inventario'))

    delta = cantidad if tipo_mov == 'ENTRADA' else -cantidad
    exito = Producto.actualizar_stock(prod_id, delta, tipo_mov, descripcion or 'Ajuste manual de stock')
    if exito:
        flash('Ajuste de inventario registrado.', 'success')
    else:
        flash('Error al registrar el ajuste.', 'danger')

    return redirect(url_for('inventario.gestion_inventario'))
