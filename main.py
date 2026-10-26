import os
from flask import Flask, render_template, session
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# Cargar variables de entorno
load_dotenv()

# Importar conexión a base de datos e inicializador automático
from database.conexion import auto_initialize_db

# Importar Blueprints (Controladores)
from views.auth import auth_bp
from views.menu import menu_bp
from views.ventas import ventas_bp
from views.inventario import inventario_bp
from views.reportes import reportes_bp
from extensions import limiter

def create_app():
    app = Flask(__name__)

    # Confiar en el proxy inverso de Render para IP y HTTPS reales
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    
    # Inicializar limitador
    limiter.init_app(app)
    
    # Configuración de clave secreta para sesiones seguras
    app.secret_key = os.getenv('SECRET_KEY', 'laureles_secret_key_2026_estudiantil_v1')
    
    # ---------------------------------------------------------
    # SEGURIDAD (Configuraciones base)
    # ---------------------------------------------------------
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # Límite global de subida: 2MB
    is_production = os.getenv('FLASK_ENV', 'development') == 'production'
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv(
            'SESSION_COOKIE_SECURE', 'true' if is_production else 'false'
        ).lower() in ('1', 'true', 'yes')
    )

    # Intentar inicializar la base de datos automáticamente si es primera ejecución
    auto_initialize_db()

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(reportes_bp)

    # Inyectar datos globales a todas las plantillas HTML
    @app.context_processor
    def inject_global_vars():
        cart = session.get('carrito', [])
        cart_count = sum(item.get('cantidad', 1) for item in cart)
        return {
            'cart_count': cart_count,
            'current_user_name': session.get('nombre'),
            'current_user_role': session.get('rol'),
            'is_admin': session.get('rol') == 'Administrador'
        }

    # Endpoint de salud para Render
    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    # Manejo de Errores Personalizados 404 y 500
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"🚀 Iniciando Tienda Escolar Virtual - I.E.D. Los Laureles en http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
