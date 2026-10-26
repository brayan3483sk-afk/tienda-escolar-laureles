import os
import matplotlib
matplotlib.use('Agg')  # Configurar backend sin interfaz gráfica para renderizado seguro en servidor
import matplotlib.pyplot as plt
import pandas as pd
from flask import Blueprint, render_template, current_app
from views.auth import admin_required
from database.conexion import fetch_all

reportes_bp = Blueprint('reportes', __name__)

# Configuración del estilo institucional para Matplotlib
COLOR_VERDE = '#1b4332'
COLOR_ROJO = '#d90429'
COLOR_AMARILLO = '#ffb703'
COLOR_AZUL = '#023e8a'
COLOR_VERDE_CLARO = '#2d6a4f'
PALETA = [COLOR_VERDE, COLOR_VERDE_CLARO, COLOR_AMARILLO, COLOR_ROJO, COLOR_AZUL, '#7209b7', '#4cc9f0']

def generar_grafico_top_productos(df_detalles, static_folder):
    """Genera gráfico de barras con los 5 productos más vendidos"""
    if df_detalles.empty:
        return 'chart_top_productos.png'

    top = df_detalles.groupby('producto_nombre')['cantidad'].sum().reset_index()
    top = top.sort_values(by='cantidad', ascending=True).tail(5)

    plt.figure(figsize=(7, 4.2))
    bars = plt.barh(top['producto_nombre'], top['cantidad'], color=COLOR_VERDE, edgecolor=COLOR_VERDE_CLARO, height=0.6)
    
    plt.title('Top 5 Productos Más Vendidos', fontsize=13, fontweight='bold', color='#1b4332', pad=15)
    plt.xlabel('Cantidad de Unidades Vendidas', fontsize=10, fontweight='bold', color='#2d6a4f')
    plt.grid(axis='x', linestyle='--', alpha=0.5)

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, f'{int(width)} u.', 
                 va='center', ha='left', fontsize=9, fontweight='bold', color='#1b4332')

    plt.tight_layout()
    chart_path = os.path.join(static_folder, 'charts', 'chart_top_productos.png')
    plt.savefig(chart_path, dpi=120, transparent=False, facecolor='#ffffff')
    plt.close()
    return 'chart_top_productos.png'

def generar_grafico_ventas_categoria(df_detalles, static_folder):
    """Genera gráfico circular (Pie Chart) de ingresos por categoría"""
    if df_detalles.empty:
        return 'chart_ventas_categoria.png'

    cat_df = df_detalles.groupby('categoria_nombre')['subtotal'].sum().reset_index()
    
    plt.figure(figsize=(6.5, 4.2))
    plt.pie(
        cat_df['subtotal'],
        labels=cat_df['categoria_nombre'],
        autopct='%1.1f%%',
        startangle=140,
        colors=PALETA[:len(cat_df)],
        textprops={'fontsize': 9, 'weight': 'bold'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )
    plt.title('Distribución de Ingresos por Categoría ($ COP)', fontsize=13, fontweight='bold', color='#1b4332', pad=15)
    plt.tight_layout()

    chart_path = os.path.join(static_folder, 'charts', 'chart_ventas_categoria.png')
    plt.savefig(chart_path, dpi=120, transparent=False, facecolor='#ffffff')
    plt.close()
    return 'chart_ventas_categoria.png'

def generar_grafico_metodos_pago(df_pedidos, static_folder):
    """Genera gráfico de dona (Donut chart) por método de pago"""
    if df_pedidos.empty:
        return 'chart_metodos_pago.png'

    pago_df = df_pedidos.groupby('metodo_pago')['total'].sum().reset_index()

    plt.figure(figsize=(6, 4))
    colors = [COLOR_VERDE, COLOR_AMARILLO]
    plt.pie(
        pago_df['total'],
        labels=pago_df['metodo_pago'],
        autopct='%1.1f%%',
        startangle=90,
        colors=colors[:len(pago_df)],
        textprops={'fontsize': 10, 'weight': 'bold'},
        wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 2}
    )
    plt.title('Comparativo de Ventas por Método de Pago', fontsize=13, fontweight='bold', color='#1b4332', pad=15)
    plt.tight_layout()

    chart_path = os.path.join(static_folder, 'charts', 'chart_metodos_pago.png')
    plt.savefig(chart_path, dpi=120, transparent=False, facecolor='#ffffff')
    plt.close()
    return 'chart_metodos_pago.png'

@reportes_bp.route('/admin/reportes')
@admin_required
def generar_reporte():
    static_folder = current_app.static_folder
    charts_dir = os.path.join(static_folder, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Obtener datos de pedidos entregados
    query_pedidos = """
        SELECT id, id_usuario, fecha, total, metodo_pago, estado
        FROM pedidos
        WHERE estado = 'ENTREGADO'
    """
    raw_pedidos = fetch_all(query_pedidos)

    query_detalles = """
        SELECT d.id_pedido, d.id_producto, p.nombre AS producto_nombre,
               c.nombre AS categoria_nombre, d.cantidad, d.precio, d.subtotal
        FROM detalle_pedido d
        INNER JOIN productos p ON d.id_producto = p.id
        INNER JOIN categorias c ON p.id_categoria = c.id
        INNER JOIN pedidos ped ON d.id_pedido = ped.id
        WHERE ped.estado = 'ENTREGADO'
    """
    raw_detalles = fetch_all(query_detalles)

    # 2. Convertir a DataFrames de Pandas
    df_pedidos = pd.DataFrame(raw_pedidos)
    df_detalles = pd.DataFrame(raw_detalles)

    # Convertir a tipos numéricos para evitar errores de Matplotlib con tipos object o string
    if not df_pedidos.empty:
        df_pedidos['total'] = pd.to_numeric(df_pedidos['total'], errors='coerce')
    
    if not df_detalles.empty:
        df_detalles['cantidad'] = pd.to_numeric(df_detalles['cantidad'], errors='coerce')
        df_detalles['precio'] = pd.to_numeric(df_detalles['precio'], errors='coerce')
        df_detalles['subtotal'] = pd.to_numeric(df_detalles['subtotal'], errors='coerce')

    # Cálculo de métricas
    total_ingresos = float(df_pedidos['total'].sum()) if not df_pedidos.empty else 0.0
    total_unidades = int(df_detalles['cantidad'].sum()) if not df_detalles.empty else 0
    total_pedidos = len(df_pedidos)
    ticket_promedio = (total_ingresos / total_pedidos) if total_pedidos > 0 else 0.0

    top_categoria = "N/A"
    if not df_detalles.empty:
        cat_sum = df_detalles.groupby('categoria_nombre')['subtotal'].sum()
        if not cat_sum.empty:
            top_categoria = cat_sum.idxmax()

    # 3. Generar gráficos con Matplotlib
    img_top = generar_grafico_top_productos(df_detalles, static_folder)
    img_cat = generar_grafico_ventas_categoria(df_detalles, static_folder)
    img_pago = generar_grafico_metodos_pago(df_pedidos, static_folder)

    # Tabla resumen de ventas por producto usando Pandas
    resumen_productos = []
    if not df_detalles.empty:
        resumen_df = df_detalles.groupby(['producto_nombre', 'categoria_nombre']).agg(
            unidades=('cantidad', 'sum'),
            total_generado=('subtotal', 'sum')
        ).reset_index().sort_values(by='total_generado', ascending=False)
        resumen_productos = resumen_df.to_dict('records')

    return render_template(
        'reportes.html',
        total_ingresos=total_ingresos,
        total_unidades=total_unidades,
        total_pedidos=total_pedidos,
        ticket_promedio=ticket_promedio,
        top_categoria=top_categoria,
        img_top=img_top,
        img_cat=img_cat,
        img_pago=img_pago,
        resumen_productos=resumen_productos
    )
