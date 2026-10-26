from database.conexion import fetch_one, fetch_all, execute_query

class Producto:
    @staticmethod
    def get_all_productos(solo_activos=True, id_categoria=None):
        query = """
            SELECT p.id, p.id_categoria, p.nombre, p.precio, p.cantidad, p.imagen, p.estado,
                   c.nombre AS categoria_nombre
            FROM productos p
            INNER JOIN categorias c ON p.id_categoria = c.id
            WHERE 1=1
        """
        params = []
        if solo_activos:
            query += " AND p.estado = 'Activo'"
        if id_categoria:
            query += " AND p.id_categoria = %s"
            params.append(id_categoria)
            
        query += " ORDER BY p.id ASC"
        return fetch_all(query, params)

    @staticmethod
    def get_producto_by_id(prod_id):
        query = """
            SELECT p.id, p.id_categoria, p.nombre, p.precio, p.cantidad, p.imagen, p.estado,
                   c.nombre AS categoria_nombre
            FROM productos p
            INNER JOIN categorias c ON p.id_categoria = c.id
            WHERE p.id = %s
        """
        return fetch_one(query, (prod_id,))

    @staticmethod
    def crear_producto(id_categoria, nombre, precio, cantidad, imagen='default_product.png'):
        query = """
            INSERT INTO productos (id_categoria, nombre, precio, cantidad, imagen, estado)
            VALUES (%s, %s, %s, %s, %s, 'Activo')
        """
        prod_id = execute_query(query, (id_categoria, nombre, precio, cantidad, imagen))
        
        # Registrar movimiento inicial de inventario
        if prod_id and cantidad > 0:
            mov_query = """
                INSERT INTO movimientos_inventario (id_producto, tipo_movimiento, cantidad, descripcion)
                VALUES (%s, 'ENTRADA', %s, 'Inventario inicial del producto')
            """
            execute_query(mov_query, (prod_id, cantidad))
        return prod_id

    @staticmethod
    def actualizar_producto(prod_id, id_categoria, nombre, precio, cantidad_nueva, imagen=None):
        prod_actual = Producto.get_producto_by_id(prod_id)
        if not prod_actual:
            return False

        diferencia = cantidad_nueva - prod_actual['cantidad']

        if imagen:
            query = """
                UPDATE productos 
                SET id_categoria = %s, nombre = %s, precio = %s, cantidad = %s, imagen = %s
                WHERE id = %s
            """
            params = (id_categoria, nombre, precio, cantidad_nueva, imagen, prod_id)
        else:
            query = """
                UPDATE productos 
                SET id_categoria = %s, nombre = %s, precio = %s, cantidad = %s
                WHERE id = %s
            """
            params = (id_categoria, nombre, precio, cantidad_nueva, prod_id)
            
        execute_query(query, params)

        # Si hubo cambio de cantidad, registrar movimiento
        if diferencia != 0:
            tipo_mov = 'ENTRADA' if diferencia > 0 else 'AJUSTE'
            mov_query = """
                INSERT INTO movimientos_inventario (id_producto, tipo_movimiento, cantidad, descripcion)
                VALUES (%s, %s, %s, 'Ajuste manual de inventario en edición')
            """
            execute_query(mov_query, (prod_id, tipo_mov, abs(diferencia)))
        return True

    @staticmethod
    def actualizar_stock(prod_id, delta_cantidad, tipo_movimiento, descripcion=''):
        """Ajusta la cantidad de stock y guarda el movimiento"""
        query_prod = "SELECT cantidad FROM productos WHERE id = %s"
        prod = fetch_one(query_prod, (prod_id,))
        if not prod:
            return False

        nueva_cantidad = prod['cantidad'] + delta_cantidad
        if nueva_cantidad < 0:
            nueva_cantidad = 0

        update_query = "UPDATE productos SET cantidad = %s WHERE id = %s"
        execute_query(update_query, (nueva_cantidad, prod_id))

        mov_query = """
            INSERT INTO movimientos_inventario (id_producto, tipo_movimiento, cantidad, descripcion)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(mov_query, (prod_id, tipo_movimiento, abs(delta_cantidad), descripcion))
        return True

    @staticmethod
    def eliminar_logico(prod_id):
        """Borrado Lógico (Soft Delete)"""
        query = "UPDATE productos SET estado = 'Inactivo' WHERE id = %s"
        return execute_query(query, (prod_id,))

    @staticmethod
    def reactivar(prod_id):
        query = "UPDATE productos SET estado = 'Activo' WHERE id = %s"
        return execute_query(query, (prod_id,))

    @staticmethod
    def get_categorias():
        query = "SELECT * FROM categorias ORDER BY id ASC"
        return fetch_all(query)

    @staticmethod
    def get_movimientos_inventario(prod_id=None):
        query = """
            SELECT m.id, m.id_producto, p.nombre AS producto_nombre, m.tipo_movimiento, m.cantidad, m.fecha, m.descripcion
            FROM movimientos_inventario m
            INNER JOIN productos p ON m.id_producto = p.id
        """
        params = []
        if prod_id:
            query += " WHERE m.id_producto = %s"
            params.append(prod_id)
        query += " ORDER BY m.fecha DESC LIMIT 50"
        return fetch_all(query, params)
