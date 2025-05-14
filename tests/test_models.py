import pytest
from flask import Flask
from website import create_app, db
from website.models import Customer, Product, Category, Order, OrderItem
from datetime import datetime

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_customer(app):
    with app.app_context():
        # Usar un email único
        customer = Customer(
            username='testuser1',
            email='test1@example.com',
            role='customer'
        )
        customer.password = 'password123'
        db.session.add(customer)
        db.session.commit()
        
        # Verificar que se creó correctamente
        saved_customer = Customer.query.filter_by(email='test1@example.com').first()
        assert saved_customer is not None
        assert saved_customer.username == 'testuser1'
        assert saved_customer.verify_password('password123')

def test_create_product(app):
    with app.app_context():
        # Primero crear una categoría
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        # Crear un producto
        product = Product(
            product_name='Test Product',
            description='Test Description',
            current_price=99.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()

        # Verificar que se creó correctamente
        saved_product = Product.query.filter_by(product_name='Test Product').first()
        assert saved_product is not None
        assert saved_product.current_price == 99.99
        assert saved_product.stock_quantity == 10
        assert saved_product.category_id == category.id

def test_create_order(app):
    with app.app_context():
        # Crear un cliente con email único
        customer = Customer(
            username='testuser2',
            email='test2@example.com',
            role='customer'
        )
        customer.password = 'password123'
        db.session.add(customer)

        # Crear una categoría y un producto
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        product = Product(
            product_name='Test Product',
            description='Test Description',
            current_price=99.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()

        # Crear una orden
        order = Order(
            customer_id=customer.id,
            status='pending',
            total=99.99,
            shipping_address='Test Address'
        )
        db.session.add(order)
        db.session.commit()

        # Verificar que se creó correctamente
        saved_order = Order.query.filter_by(customer_id=customer.id).first()
        assert saved_order is not None
        assert saved_order.status == 'pending'
        assert saved_order.total == 99.99

def test_customer_relationships(app):
    with app.app_context():
        # Crear un cliente con email único
        customer = Customer(
            username='testuser3',
            email='test3@example.com',
            role='customer'
        )
        customer.password = 'password123'
        db.session.add(customer)

        # Crear una categoría y un producto
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        product = Product(
            product_name='Test Product',
            description='Test Description',
            current_price=99.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()

        # Crear una orden para el cliente
        order = Order(
            customer_id=customer.id,
            status='pending',
            total=99.99,
            shipping_address='Test Address'
        )
        db.session.add(order)
        db.session.commit()

        # Verificar la relación
        assert len(customer.orders) == 1
        assert customer.orders[0].status == 'pending'
        assert customer.orders[0].total == 99.99 