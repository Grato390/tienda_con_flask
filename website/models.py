from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from . import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(1000), nullable=True)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    discount_percentage = db.Column(db.Float, default=0.0)
    descuento = db.Column(db.Float, default=0.0)  # Nuevo campo para descuento
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    ventas = db.relationship('Vender', backref='product', lazy=True, foreign_keys='Vender.product_link')  # Cambiado de carts a ventas
    orders = db.relationship('Order', backref='product', lazy=True)
    favorites = db.relationship('Favorite', backref='product', lazy=True)
    
    # Método para calcular el precio con descuento
    def precio_con_descuento(self):
        if self.descuento > 0:
            return self.current_price * (1 - self.descuento / 100)
        return self.current_price

class Vender(db.Model):  # Cambiado de Cart a Vender
    id = db.Column(db.Integer, primary_key=True)
    customer_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    ventas = db.relationship('Vender', backref='user', lazy=True, foreign_keys='Vender.customer_link')  # Cambiado de carts a ventas
    orders = db.relationship('Order', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    
    # Método para verificar la contraseña
    def verify_password(self, password):
        return self.password == password  # En producción, usar hash











