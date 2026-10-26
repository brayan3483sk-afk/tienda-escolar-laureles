from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from views.auth import login_required, admin_required
from models.producto import Producto
from models.pedido import Pedido

ventas_bp = Blueprint('ventas', __name__)

def get_session_cart():
    if 'carrito' not in session:
        session['carrito'] = []
    return session['carrito']

def save_session_cart(cart):
    session['carrito'] = cart
    session.modified = True

@ventas_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    prod_id = request.form.get('id_producto', type=int)
    cantidad = request.form.get('cantidad', type=int, default=1)
    
    if not prod_id or cantidad <= 0:
        flash('Datos de producto no válidos.', 'danger')
        return redirect(url_for('menu.index'))

    prod = Producto.get_producto_by_id(prod_id)
    if not prod or prod['estado'] != 'Activo':
        flash('El producto seleccionado no está disponible.', 'danger')
        return redirect(url_for('menu.index'))

    if prod['cantidad'] <= 0:
        flash('El producto está agotado.', 'warning')
        return redirect(url_for('menu.index'))

    cart = get_session_cart()
    
    # Buscar si ya existe en el carrito
    item_existente = next((item for item in cart if item['id'] == prod_id), None)
    
    cant_actual = item_existente['cantidad'] if item_existente else 0
    nueva_cant = cant_actual + cantidad

    if nueva_cant > prod['cantidad']:
        flash(f'Solo hay {prod["cantidad"]} unidades disponibles en stock.', 'warning')
        return redirect(url_for('menu.index'))

    if item_existente:
        item_existente['cantidad'] = nueva_cant
        item_existente['subtotal'] = float(prod['precio']) * nueva_cant
    else:
        cart.append({
            'id': prod['id'],
            'nombre': prod['nombre'],
            'precio': float(prod['precio']),
            'imagen': prod['imagen'],
            'cantidad': cantidad,
            'subtotal': float(prod['precio']) * cantidad
        })

    save_session_cart(cart)
    flash(f'¡"{prod["nombre"]}" agregado al carrito!', 'success')
    
    if request.form.get('comprar_ahora'):
        return redirect(url_for('ventas.ver_carrito'))
        
    return redirect(url_for('menu.index'))

@ventas_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    prod_id = request.form.get('id_producto', type=int)
    nueva_cantidad = request.form.get('cantidad', type=int, default=1)

    cart = get_session_cart()
    item = next((i for i in cart if i['id'] == prod_id), None)
    
    if item:
        prod = Producto.get_producto_by_id(prod_id)
        if prod and nueva_cantidad <= prod['cantidad']:
            if nueva_cantidad > 0:
                item['cantidad'] = nueva_cantidad
                item['subtotal'] = item['precio'] * nueva_cantidad
            else:
                cart.remove(item)
            save_session_cart(cart)
            flash('Carrito actualizado.', 'info')
        else:
            flash(f'Stock disponible máximo: {prod["cantidad"] if prod else 0}', 'warning')
            
    return redirect(url_for('ventas.ver_carrito'))

@ventas_bp.route('/cart/remove/<int:prod_id>', methods=['POST', 'GET'])
@login_required
def remove_from_cart(prod_id):
    cart = get_session_cart()
    cart = [i for i in cart if i['id'] != prod_id]
    save_session_cart(cart)
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('ventas.ver_carrito'))

@ventas_bp.route('/cart/clear', methods=['POST', 'GET'])
@login_required
def clear_cart():
    save_session_cart([])
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('ventas.ver_carrito'))

@ventas_bp.route('/carrito')
@login_required
def ver_carrito():
    cart = get_session_cart()
    total = sum(item['subtotal'] for item in cart)
    
    # Agregar stock disponible a los items para el HTML
    for item in cart:
        prod = Producto.get_producto_by_id(item['id'])
        item['stock_disponible'] = prod['cantidad'] if prod else 0

    return render_template('carrito.html', carrito=cart, total=total)

@ventas_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = get_session_cart()
    if not cart:
        flash('Su carrito está vacío.', 'warning')
        return redirect(url_for('menu.index'))

    metodo_pago = request.form.get('metodo_pago')
    if metodo_pago not in ['EFECTIVO', 'TRANSFERENCIA']:
        flash('Seleccione un método de pago válido.', 'danger')
        return redirect(url_for('ventas.ver_carrito'))

    user_id = session.get('user_id')
    exito, mensaje_o_id = Pedido.crear_pedido(user_id, cart, metodo_pago)

    if exito:
        save_session_cart([]) # Vaciar carrito tras compra exitosa
        pedido_id = mensaje_o_id
        if metodo_pago == 'TRANSFERENCIA':
            flash(f'¡Pedido #{pedido_id} creado con éxito! Presente su comprobante en su celular al personal de la tienda para la validación presencial.', 'success')
        else:
            flash(f'¡Pedido #{pedido_id} creado con éxito! Pagará en efectivo al reclamar su producto.', 'success')
        return redirect(url_for('ventas.mis_pedidos'))
    else:
        flash(f'Error al procesar el pedido: {mensaje_o_id}', 'danger')
        return redirect(url_for('ventas.ver_carrito'))

@ventas_bp.route('/mis-pedidos')
@login_required
def mis_pedidos():
    user_id = session.get('user_id')
    pedidos_lista = Pedido.get_pedidos_by_usuario(user_id)
    return render_template('mis_pedidos.html', pedidos=pedidos_lista)

@ventas_bp.route('/mis-pedidos/<int:pedido_id>')
@login_required
def ver_detalle_pedido(pedido_id):
    user_id = session.get('user_id')
    es_admin = session.get('rol') == 'Administrador'
    
    # RLS simulado: Solo los administradores pueden ignorar el user_id
    id_para_filtro = None if es_admin else user_id
    pedido, detalles = Pedido.get_pedido_con_detalles(pedido_id, user_id=id_para_filtro)
    
    if not pedido:
        flash('Pedido no encontrado o no autorizado.', 'danger')
        return redirect(url_for('ventas.mis_pedidos'))
        
    return render_template('detalle_pedido.html', pedido=pedido, detalles=detalles)

# -----------------------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN DE PEDIDOS
# -----------------------------------------------------------------------------

@ventas_bp.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    filtro = request.args.get('estado', type=str)
    pedidos_lista = Pedido.get_all_pedidos(filtro_estado=filtro)
    return render_template('admin_pedidos.html', pedidos=pedidos_lista, filtro_actual=filtro)

@ventas_bp.route('/admin/pedidos/cambiar-estado', methods=['POST'])
@admin_required
def cambiar_estado():
    pedido_id = request.form.get('pedido_id', type=int)
    nuevo_estado = request.form.get('nuevo_estado')
    
    exito, mensaje = Pedido.cambiar_estado_pedido(pedido_id, nuevo_estado)
    if exito:
        flash(f'Pedido #{pedido_id}: {mensaje}', 'success')
    else:
        flash(f'Error al actualizar pedido: {mensaje}', 'danger')
        
    return redirect(url_for('ventas.admin_pedidos'))
