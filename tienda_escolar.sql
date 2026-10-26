-- =============================================================================
-- BASE DE DATOS: TIENDA ESCOLAR VIRTUAL
-- INSTITUCIÓN EDUCATIVA DISTRITAL LOS LAURELES
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `tienda_escolar` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `tienda_escolar`;

-- -----------------------------------------------------------------------------
-- 1. TABLA: usuarios
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `movimientos_inventario`;
DROP TABLE IF EXISTS `detalle_pedido`;
DROP TABLE IF EXISTS `pedidos`;
DROP TABLE IF EXISTS `productos`;
DROP TABLE IF EXISTS `categorias`;
DROP TABLE IF EXISTS `usuarios`;

CREATE TABLE `usuarios` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(100) NOT NULL,
  `usuario` VARCHAR(50) NOT NULL UNIQUE,
  `contrasena` VARCHAR(255) NOT NULL,
  `rol` ENUM('Administrador', 'Estudiante') NOT NULL DEFAULT 'Estudiante',
  `estado` ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. TABLA: categorias
-- -----------------------------------------------------------------------------
CREATE TABLE `categorias` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nombre` VARCHAR(50) NOT NULL,
  `descripcion` TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. TABLA: productos
-- -----------------------------------------------------------------------------
CREATE TABLE `productos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_categoria` INT NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `precio` DECIMAL(10, 2) NOT NULL,
  `cantidad` INT NOT NULL DEFAULT 0,
  `imagen` VARCHAR(255) DEFAULT 'default_product.png',
  `estado` ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
  FOREIGN KEY (`id_categoria`) REFERENCES `categorias`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. TABLA: pedidos
-- -----------------------------------------------------------------------------
CREATE TABLE `pedidos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_usuario` INT NOT NULL,
  `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `total` DECIMAL(10, 2) NOT NULL,
  `metodo_pago` ENUM('EFECTIVO', 'TRANSFERENCIA') NOT NULL,
  `estado` ENUM('PENDIENTE', 'ENTREGADO', 'CANCELADO') NOT NULL DEFAULT 'PENDIENTE',
  FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. TABLA: detalle_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE `detalle_pedido` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_pedido` INT NOT NULL,
  `id_producto` INT NOT NULL,
  `cantidad` INT NOT NULL,
  `precio` DECIMAL(10, 2) NOT NULL,
  `subtotal` DECIMAL(10, 2) NOT NULL,
  FOREIGN KEY (`id_pedido`) REFERENCES `pedidos`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`id_producto`) REFERENCES `productos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. TABLA: movimientos_inventario
-- -----------------------------------------------------------------------------
CREATE TABLE `movimientos_inventario` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `id_producto` INT NOT NULL,
  `tipo_movimiento` ENUM('ENTRADA', 'SALIDA', 'AJUSTE') NOT NULL,
  `cantidad` INT NOT NULL,
  `fecha` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `descripcion` VARCHAR(255),
  FOREIGN KEY (`id_producto`) REFERENCES `productos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- DATOS SEMILLA (DATA SEEDING)
-- =============================================================================

-- 1. Usuarios por defecto (Admin: admin123 | Student: estudiante123)
INSERT INTO `usuarios` (`id`, `nombre`, `usuario`, `contrasena`, `rol`, `estado`) VALUES
(1, 'Administrador Laureles', 'admin', 'scrypt:32768:8:1$EFJ1OP9z6hLEAwkT$080385ee76b838e7760a426f0c76cc6eeefa999c1cce2ceb0f90da91c26096fe4fdc2e11773dfc99965210987912cb49c3241d44d393e639e0388cfd3651e7ba', 'Administrador', 'Activo'),
(2, 'Juan Pérez (Estudiante)', 'estudiante', 'scrypt:32768:8:1$oncOgonYfSJjvkpK$025b65f6a4f821d28769c4d043d6384af8a12302647e8c3db0f029583ff86a63986d925b9cf9b2ed25e573f3b0576b249f79456657442df902757a012028a77d', 'Estudiante', 'Activo');

-- 2. Categorías (5 categorías)
INSERT INTO `categorias` (`id`, `nombre`, `descripcion`) VALUES
(1, 'Bebidas', 'Bebidas frías, jugos naturales, agua y gaseosas refrescantes'),
(2, 'Snacks y Pasabocas', 'Empanadas, sándwiches, papas fritas y snacks horneados'),
(3, 'Frutas y Saludables', 'Ensaladas de frutas, yogurt, frutos secos y opciones fit'),
(4, 'Almuerzos y Combos', 'Combos ejecutivos escolares, platos calientes y especiales'),
(5, 'Dulcería y Postres', 'Galletas, chocolates, muffins y postres caseros');

-- 3. Productos (10 productos)
INSERT INTO `productos` (`id`, `id_categoria`, `nombre`, `precio`, `cantidad`, `imagen`, `estado`) VALUES
(1, 1, 'Jugo Natural de Naranja (400ml)', 3500.00, 25, 'jugo_naranja.png', 'Activo'),
(2, 2, 'Empanada Hornea de Carne', 2500.00, 40, 'empanada_carne.png', 'Activo'),
(3, 3, 'Ensalada de Frutas Especial', 4500.00, 15, 'ensalada_frutas.png', 'Activo'),
(4, 4, 'Combo Almuerzo Escolar Laureles', 8500.00, 30, 'combo_almuerzo.png', 'Activo'),
(5, 2, 'Sándwich Especial Jamón y Queso', 4000.00, 20, 'sandwich.png', 'Activo'),
(6, 1, 'Agua Mineral Natural 500ml', 2000.00, 50, 'agua_mineral.png', 'Activo'),
(7, 5, 'Muffin Artesanal de Arándanos', 3000.00, 15, 'muffin_arandanos.png', 'Activo'),
(8, 3, 'Yogurt Griego con Granola', 3800.00, 18, 'yogurt_granola.png', 'Activo'),
(9, 2, 'Papas Crocantes Paquete', 2500.00, 35, 'papas_fritas.png', 'Activo'),
(10, 5, 'Chocolatina Institucional 50g', 1500.00, 45, 'chocolatina.png', 'Activo');

-- 4. Movimientos iniciales de inventario (Stock inicial)
INSERT INTO `movimientos_inventario` (`id_producto`, `tipo_movimiento`, `cantidad`, `descripcion`) VALUES
(1, 'ENTRADA', 25, 'Carga inicial de inventario'),
(2, 'ENTRADA', 40, 'Carga inicial de inventario'),
(3, 'ENTRADA', 15, 'Carga inicial de inventario'),
(4, 'ENTRADA', 30, 'Carga inicial de inventario'),
(5, 'ENTRADA', 20, 'Carga inicial de inventario'),
(6, 'ENTRADA', 50, 'Carga inicial de inventario'),
(7, 'ENTRADA', 15, 'Carga inicial de inventario'),
(8, 'ENTRADA', 18, 'Carga inicial de inventario'),
(9, 'ENTRADA', 35, 'Carga inicial de inventario'),
(10, 'ENTRADA', 45, 'Carga inicial de inventario');

-- 5. Pedido semilla de demostración
INSERT INTO `pedidos` (`id`, `id_usuario`, `fecha`, `total`, `metodo_pago`, `estado`) VALUES
(1, 2, NOW(), 8500.00, 'TRANSFERENCIA', 'PENDIENTE'),
(2, 2, NOW(), 6000.00, 'EFECTIVO', 'ENTREGADO');

INSERT INTO `detalle_pedido` (`id_pedido`, `id_producto`, `cantidad`, `precio`, `subtotal`) VALUES
(1, 4, 1, 8500.00, 8500.00),
(2, 1, 1, 3500.00, 3500.00),
(2, 2, 1, 2500.00, 2500.00);
