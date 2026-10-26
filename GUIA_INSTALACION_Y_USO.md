# 📖 Guía de Exportación, Instalación y Uso: Tienda Escolar Virtual

Esta guía detalla los pasos necesarios para exportar correctamente el proyecto, instalarlo en una nueva computadora sin problemas de entorno y cómo utilizar la plataforma de la Institución Educativa Distrital Los Laureles.

---

## 📦 1. Cómo Exportar el Proyecto (Evitar errores)

Para llevarte el proyecto a otra computadora, memoria USB o subirlo a un repositorio (como GitHub), **NO debes copiar la carpeta `venv` ni `__pycache__`**. Copiar estas carpetas causa errores en otras computadoras porque contienen rutas y configuraciones específicas del equipo original.

### Pasos para exportar (crear un ZIP limpio):
1. Ve a la carpeta de tu proyecto (`TIENDA_ESCOLAR`).
2. Selecciona todos los archivos y carpetas, **EXCEPTO**:
   - `venv` (El entorno virtual).
   - `__pycache__` (Archivos temporales de Python).
3. Haz clic derecho y selecciona "Comprimir en archivo ZIP" o "Enviar a -> Carpeta comprimida (en zip)".
4. Lleva ese archivo ZIP a la otra computadora.

---

## 🛠️ 2. Cómo Importar e Instalar en otra Computadora

Una vez que hayas descomprimido el archivo ZIP en la nueva computadora, sigue estos pasos para configurarlo desde cero.

### Paso A: Requisitos Previos
- Tener instalado **Python 3.9 o superior** (Asegúrate de marcar la casilla "Add Python to PATH" durante su instalación).
- Tener instalado **XAMPP**, **WAMP** o cualquier servidor de base de datos MySQL local.

### Paso B: Configuración de la Base de Datos
1. Abre el panel de control de XAMPP y enciende los servicios de **Apache** y **MySQL**.
2. Entra a phpMyAdmin desde tu navegador (usualmente `http://localhost/phpmyadmin/`).
3. Crea una base de datos nueva llamada `tienda_escolar`.
4. Ve a la pestaña "Importar", selecciona el archivo `tienda_escolar.sql` que viene en la carpeta del proyecto y presiona en "Importar" o "Ejecutar" para cargar todas las tablas y datos base.

### Paso C: Creación del Entorno Virtual e Instalación de Dependencias
Abre una terminal (Símbolo del sistema, PowerShell o la terminal integrada de VS Code) dentro de la carpeta del proyecto y ejecuta en orden:

1. **Crear un nuevo entorno virtual limpio:**
   ```bash
   python -m venv venv
   ```
   *(Esto creará una nueva carpeta `venv` adaptada a esta computadora).*

2. **Activar el entorno virtual:**
   - En **Windows** (PowerShell / CMD):
     ```bash
     .\venv\Scripts\activate
     ```
   - En **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```
   *(Sabrás que está activado porque aparecerá `(venv)` al inicio de tu línea de comandos).*

3. **Instalar los paquetes del proyecto:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Esto descargará Flask, Pandas, Matplotlib, y todas las herramientas necesarias).*

### Paso D: Configurar Variables de Entorno
1. En la carpeta del proyecto, busca el archivo `.env.example`.
2. Cóplialo y renombra la copia simplemente como `.env`.
3. Ábrelo en un bloc de notas o editor de texto. Asegúrate de que los datos de conexión a MySQL sean correctos para esa computadora (por defecto en XAMPP el usuario es `root` y la clave está vacía):
   ```env
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=tienda_escolar
   ```

---

## 🚀 3. Guía de Uso del Sistema

Una vez configurado todo lo anterior, puedes iniciar la aplicación.

### Iniciar el servidor
Asegúrate de tener el entorno virtual activado (`(venv)`) y ejecuta:
```bash
python main.py
```
Abre tu navegador y entra a: **`http://localhost:5000`**

### Roles de Usuario y Accesos de Prueba
En la pantalla de inicio de sesión, verás un recuadro de ayuda. Puedes usar estas credenciales para probar los roles:
- **Administrador:** `admin` / `admin123`
- **Estudiante (Cliente):** `estudiante` / `estudiante123`

### Funciones Principales:

#### 🎓 Vista Estudiante (Cliente)
1. **Catálogo de Productos:** Podrás ver los productos ofrecidos por la cafetería y agregarlos al carrito con sus respectivas cantidades.
2. **Carrito de Compras:** Revisa los productos añadidos, visualiza el costo total y confirma tu pedido.
3. **Opciones de Pago:** Puedes elegir pagar en **Efectivo** (pagas al recoger en la cafetería) o mediante **Transferencia bancaria/Nequi** (simulado en el sistema con generación de comprobante QR).
4. **Mis Pedidos:** Un panel para ver el estado en tiempo real de tus pedidos (Pendiente, Pagado, Entregado, Cancelado).

#### 🛡️ Vista Administrador (Gestión)
1. **Dashboard Principal:** Resumen de cuántas ventas se han hecho hoy y notificaciones de pedidos entrantes.
2. **Inventario:** 
   - Añadir nuevos productos, subir imágenes representativas y fijar precios.
   - Administrar categorías (Comidas, Bebidas, Dulces).
   - Controlar las cantidades disponibles (Stock) para evitar que se vendan productos agotados.
3. **Gestión de Pedidos:** 
   - Cola de atención de la cafetería. Aquí se reciben los pedidos de los estudiantes.
   - Funcionalidad para marcar pedidos como preparados, pagados o entregados.
4. **Reportes y Analítica Avanzada:**
   - Esta vista utiliza `Pandas` y `Matplotlib` para generar gráficos en tiempo real.
   - Incluye gráficos de Productos más vendidos, Distribución de ingresos por categoría, y Métodos de pago preferidos.
   - Ideal para visualizar qué productos son rentables en la institución.

---
**💡 Solución a Errores Comunes:**
- Si al ejecutar `python main.py` te sale un error como `ModuleNotFoundError: No module named 'flask'`, significa que olvidaste activar el entorno virtual o no corriste el comando `pip install -r requirements.txt`. Actívalo (`.\venv\Scripts\activate`) e intenta de nuevo.
