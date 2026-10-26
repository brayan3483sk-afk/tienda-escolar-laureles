import os
import io
import base64
import qrcode
from flask import Blueprint, render_template, request, session, current_app
from views.auth import login_required
from models.producto import Producto

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/')
@menu_bp.route('/menu')
def index():
    cat_id = request.args.get('categoria', type=int)
    search_query = request.args.get('q', type=str, default='').strip()

    productos = Producto.get_all_productos(solo_activos=True, id_categoria=cat_id)
    categorias = Producto.get_categorias()

    if search_query:
        productos = [p for p in productos if search_query.lower() in p['nombre'].lower()]

    # Generar QR dinámico para sustentación académica (Plan B Ngrok)
    ngrok_url = os.getenv('NGROK_URL', '').strip()
    qr_base64 = None
    if ngrok_url:
        try:
            qr_img = qrcode.make(ngrok_url)
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error al generar código QR: {e}")

    return render_template(
        'menu.html',
        productos=productos,
        categorias=categorias,
        cat_seleccionada=cat_id,
        search_query=search_query,
        ngrok_url=ngrok_url,
        qr_base64=qr_base64
    )
