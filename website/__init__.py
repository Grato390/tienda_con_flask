from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import os

DB_NAME = "database.sqlite3"
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hbnwdvbn ajnbsjn ahe'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    db.init_app(app)
    
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Importamos User después de inicializar db
    from .models import User
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    from .views import views
    from .auth import auth
    from .admin import admin
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    
    # Creamos la base de datos si no existe
    with app.app_context():
        db.create_all()
    
    return app

