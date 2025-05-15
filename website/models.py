from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
CUSTOM_ID = 'customer.id'

class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    role = db.Column(db.String(20), default='customer')
    is_first_login = db.Column(db.Boolean, default=True)
    force_password_change = db.Column(db.Boolean, default=False)
    profile_picture = db.Column(db.String(200))
    bio = db.Column(db.Text)
    preferences = db.Column(db.Text)
    security_questions = db.Column(db.Text)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    login_attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)
    locked_until = db.Column(db.DateTime)

    cart_items = db.relationship('Cart', backref=db.backref('customer', lazy=True))
    orders = db.relationship('Order', backref='customer')

    @property
    def is_admin(self):
        return self.role in ['admin', 'super_admin']

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    def set_admin(self, is_admin):
        self.role = 'admin' if is_admin else 'customer'

    def set_super_admin(self, is_super_admin):
        self.role = 'super_admin' if is_super_admin else 'customer'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_preferences(self):
        if self.preferences:
            return json.loads(self.preferences)
        return {}

    def set_preferences(self, preferences):
        self.preferences = json.dumps(preferences)

    def get_security_questions(self):
        """Obtiene las preguntas de seguridad del JSON"""
        if self.security_questions:
            return json.loads(self.security_questions)
        return {}

    def set_security_questions(self, questions):
        """Guarda las preguntas de seguridad en formato JSON"""
        if isinstance(questions, dict):
            self.security_questions = json.dumps(questions)
        else:
            raise ValueError("Las preguntas deben ser un diccionario")

    def verify_security_answer(self, question_id, answer):
        """Verifica si la respuesta a una pregunta de seguridad es correcta"""
        questions = self.get_security_questions()
        if question_id in questions:
            return questions[question_id]['answer'].lower() == answer.lower()
        return False

    def __str__(self):
        return '<Customer %r>' % self.id


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float)
    in_stock = db.Column(db.Boolean, default=True)  # Indica si el producto está disponible para la venta
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)  # Cantidad exacta en stock
    flash_sale = db.Column(db.Boolean, default=False)
    product_picture = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey(CUSTOM_ID), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    category = db.relationship('Category', backref=db.backref('products', lazy=True))
    order_items = db.relationship('OrderItem', backref='product', lazy=True, cascade='all, delete-orphan')
    carts = db.relationship('Cart', backref=db.backref('product', lazy=True), cascade='all, delete-orphan')
    creator = db.relationship('Customer', backref=db.backref('products_created', lazy=True))

    def __str__(self):
        return f'<Product {self.product_name}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey(CUSTOM_ID), nullable=False)
    status = db.Column(db.String(20), default='pending')
    total = db.Column(db.Float, default=0.0)
    shipping_address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __str__(self):
        return '<Order %r>' % self.id


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return '<OrderItem %r>' % self.id


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey(CUSTOM_ID), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    @property
    def customer_link(self):
        return self.customer
    
    @customer_link.setter
    def customer_link(self, value):
        if isinstance(value, int):
            self.customer_id = value
        else:
            self.customer = value
    
    @property
    def product_link(self):
        return self.product
    
    @product_link.setter
    def product_link(self, value):
        if isinstance(value, int):
            self.product_id = value
        else:
            self.product = value
    
    def __str__(self):
        return '<Cart %r>' % self.id


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # La relación con productos se maneja desde el modelo Product

    def __repr__(self):
        return f'<Category {self.name}>'











