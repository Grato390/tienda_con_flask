from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from os import path
import os
import secrets
import string
from dotenv import load_dotenv
load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.sqlite3"
csrf = CSRFProtect()
mail = Mail()

# Clave de seguridad para el administrador (debería estar en una variable de entorno)
ADMIN_SECURITY_KEY = os.environ.get('ADMIN_SECURITY_KEY', 'your-super-secret-key-here')


def generate_secure_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_super_admin():
    """Create a super admin user if none exists."""
    from .models import Customer
    super_admin = Customer.query.filter_by(role='super_admin').first()
    if not super_admin:
        password = os.environ.get('SUPER_ADMIN_PASSWORD', 'default-password')
        super_admin = Customer(
            email='admin@tienda.com',
            username='super_admin',
            role='super_admin',
            force_password_change=True,
            is_first_login=True
        )
        super_admin.password = password
        db.session.add(super_admin)
        db.session.commit()
        print('='*50)
        print('DATOS DE ACCESO DEL SUPER ADMIN:')
        print('Email: admin@tienda.com')
        print('Usuario: super_admin')
        print('Contraseña: admin123')
        print('='*50)


def create_database(app):
    with app.app_context():
        # Solo crear las tablas si no existen
        db.create_all()
        
        # Verificar si ya existe un super admin
        from .models import Customer
        super_admin = Customer.query.filter_by(role='super_admin').first()
        if not super_admin:
            create_super_admin()
    print('Database initialized!')


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Usar una clave secreta desde una variable de entorno y lanzar un error si no está configurada
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError("La variable de entorno 'SECRET_KEY' no está configurada. Configúrala antes de iniciar la aplicación.")
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, DB_NAME)}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'website/static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Configuración para servir archivos estáticos desde media
    @app.route('/media/<path:filename>')
    def media(filename):
        return send_from_directory('../media', filename)

    # Configuración de Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@tutienda.com')

    # Crear la carpeta instance si no existe
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Inicializar extensiones
    db.init_app(app)
    # Inicializar CSRF después de crear la aplicación
    csrf = CSRFProtect()
    csrf.init_app(app)
    mail.init_app(app)
    
    # Configurar CSRF para ignorar rutas específicas
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import Customer, Cart, Product, Order, Category

    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    # Importar blueprints después de inicializar las extensiones
    from .views import views
    from .auth import auth
    from .admin import admin as admin_blueprint
    from .product import product_blueprint

    # Registrar blueprints
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(product_blueprint, url_prefix='/product')

    create_database(app)
    
    # Asegurar que el token CSRF esté disponible en todas las plantillas
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    return app

