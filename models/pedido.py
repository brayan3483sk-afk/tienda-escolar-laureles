from database.conexion import (
    IS_POSTGRES,
    execute_query,
    fetch_all,
    fetch_one,
    get_db_connection,
    get_dict_cursor,
)

class Pedido:
    @staticmethod
    def crear_pedido(id_usuario, items_carrito, metodo_pago):
        """
        Crea un pedido con sus detalles y actualiza el inventario en una transacción segura.
        items_carrito: lista de dicts [{'id': int, 'nombre': str, 'precio': float, 'cantidad': int, 'subtotal': float}]
        """
        if not items_carrito:
            return False, "El carrito está vacío."

        if metodo_pago not in ['EFECTIVO', 'TRANSFERENCIA']:
            return False, "Método de pago no válido."

        # 1. Validar stock de todos los productos primero
        for item in items_carrito:
            prod = fetch_one("SELECT cantidad, nombre, estado FROM productos WHERE id = %s", (item['id'],))
            if not prod or prod['estado'] != 'Activo':
                return False, f"El producto {item['nombre']} ya no está disponible."
            if prod['cantidad'] < item['cantidad']:
                return False, f"Stock insuficiente para {item['nombre']}. Stock disponible: {prod['cantidad']}."

        total_pedido = sum(float(item['subtotal']) for item in items_carrito)

        connection = get_db_connection()
        if not connection:
            return False, "Error de conexión con la base de datos."

        cursor = get_dict_cursor(connection)
        try:
            # 2. Insertar pedido cabecera
            if IS_POSTGRES:
                query_pedido = """
                    INSERT INTO pedidos (id_usuario, fecha, total, metodo_pago, estado)
                    VALUES (%s, NOW(), %s, %s, 'PENDIENTE')
                    RETURNING id
                """
                cursor.execute(query_pedido, (id_usuario, total_pedido, metodo_pago))
                pedido_id = cursor.fetchone()['id']
            else:
                query_pedido = """
                    INSERT INTO pedidos (id_usuario, fecha, total, metodo_pago, estado)
                    VALUES (%s, NOW(), %s, %s, 'PENDIENTE')
                """
                cursor.execute(query_pedido, (id_usuario, total_pedido, metodo_pago))
                pedido_id = cursor.lastrowid

            # 3. Insertar detalles y descontar inventario
            for item in items_carrito:
                query_detalle = """
                    INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query_detalle, (pedido_id, item['id'], item['cantidad'], item['precio'], item['subtotal']))

                # Descontar stock
                query_stock = "UPDATE productos SET cantidad = cantidad - %s WHERE id = %s"
                cursor.execute(query_stock, (item['cantidad'], item['id']))

                # Registrar movimiento de salida
                desc_mov = f"Venta registrada - Pedido #{pedido_id} ({metodo_pago})"
                query_mov = """
                    INSERT INTO movimientos_inventario (id_producto, tipo_movimiento, cantidad, descripcion)
                    VALUES (%s, 'SALIDA', %s, %s)
                """
                cursor.execute(query_mov, (item['id'], item['cantidad'], desc_mov))

            connection.commit()
            return True, pedido_id
        except Exception as e:
            connection.rollback()
            print(f"❌ Error al procesar el pedido: {e}")
            return False, f"Error al procesar el pedido: {str(e)}"
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def get_pedidos_by_usuario(id_usuario):
        query = """
            SELECT p.id, p.fecha, p.total, p.metodo_pago, p.estado,
                   COUNT(d.id) AS total_items
            FROM pedidos p
            LEFT JOIN detalle_pedido d ON p.id = d.id_pedido
            WHERE p.id_usuario = %s
            GROUP BY p.id
            ORDER BY p.fecha DESC
        """
        return fetch_all(query, (id_usuario,))

    @staticmethod
    def get_all_pedidos(filtro_estado=None):
        if IS_POSTGRES:
            descripcion_sql = "STRING_AGG(d.cantidad || 'x ' || pr.nombre, ', ')"
        else:
            descripcion_sql = "GROUP_CONCAT(CONCAT(d.cantidad, 'x ', pr.nombre) SEPARATOR ', ')"
        query = f"""
            SELECT p.id, p.id_usuario, u.nombre AS usuario_nombre, u.usuario AS usuario_username,
                   p.fecha, p.total, p.metodo_pago, p.estado,
                   {descripcion_sql} AS descripcion_productos
            FROM pedidos p
            INNER JOIN usuarios u ON p.id_usuario = u.id
            LEFT JOIN detalle_pedido d ON p.id = d.id_pedido
            LEFT JOIN productos pr ON d.id_producto = pr.id
        """
        params = []
        if filtro_estado:
            query += " WHERE p.estado = %s"
            params.append(filtro_estado)
        
        query += (
            " GROUP BY p.id, p.id_usuario, u.nombre, u.usuario, p.fecha, p.total, "
            "p.metodo_pago, p.estado ORDER BY p.fecha DESC"
        )
        return fetch_all(query, params)

    @staticmethod
    def get_pedido_con_detalles(pedido_id, user_id=None):
        query_pedido = """
            SELECT p.id, p.id_usuario, u.nombre AS usuario_nombre, u.usuario AS usuario_username,
                   p.fecha, p.total, p.metodo_pago, p.estado
            FROM pedidos p
            INNER JOIN usuarios u ON p.id_usuario = u.id
            WHERE p.id = %s
        """
        params = [pedido_id]
        if user_id:
            query_pedido += " AND p.id_usuario = %s"
            params.append(user_id)
            
        pedido = fetch_one(query_pedido, params)
        if not pedido:
            return None, []

        query_detalles = """
            SELECT d.id, d.id_producto, pr.nombre AS producto_nombre, pr.imagen,
                   d.cantidad, d.precio, d.subtotal
            FROM detalle_pedido d
            INNER JOIN productos pr ON d.id_producto = pr.id
            WHERE d.id_pedido = %s
        """
        detalles = fetch_all(query_detalles, (pedido_id,))
        return pedido, detalles

    @staticmethod
    def cambiar_estado_pedido(pedido_id, nuevo_estado):
        if nuevo_estado not in ['PENDIENTE', 'ENTREGADO', 'CANCELADO']:
            return False, "Estado no válido."

        pedido, detalles = Pedido.get_pedido_con_detalles(pedido_id)
        if not pedido:
            return False, "Pedido no encontrado."

        estado_anterior = pedido['estado']
        if estado_anterior == nuevo_estado:
            return True, "El pedido ya se encuentra en ese estado."

        # Si el pedido se cancela, restaurar el inventario
        if nuevo_estado == 'CANCELADO' and estado_anterior != 'CANCELADO':
            connection = get_db_connection()
            if not connection:
                return False, "Error de conexión."
            cursor = connection.cursor()
            try:
                cursor.execute("UPDATE pedidos SET estado = %s WHERE id = %s", (nuevo_estado, pedido_id))
                for item in detalles:
                    cursor.execute("UPDATE productos SET cantidad = cantidad + %s WHERE id = %s", (item['cantidad'], item['id_producto']))
                    desc = f"Devolución por cancelación de Pedido #{pedido_id}"
                    cursor.execute("""
                        INSERT INTO movimientos_inventario (id_producto, tipo_movimiento, cantidad, descripcion)
                        VALUES (%s, 'AJUSTE', %s, %s)
                    """, (item['id_producto'], item['cantidad'], desc))
                connection.commit()
                return True, "Pedido cancelado y stock devuelto al inventario."
            except Exception as e:
                connection.rollback()
                return False, str(e)
            finally:
                cursor.close()
                connection.close()

        # Para otros estados (ej. PENDIENTE -> ENTREGADO)
        query = "UPDATE pedidos SET estado = %s WHERE id = %s"
        execute_query(query, (nuevo_estado, pedido_id))
        return True, f"Estado actualizado a {nuevo_estado}."
