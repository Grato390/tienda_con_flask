import pytest
from flask import Flask
from website import create_app
from website import db
import pytest
from flask import Flask
from website import create_app
from website.models import Product, Customer, Order
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_admin_page_redirects_to_404_if_not_super_admin(client):
    # Simula un login de un usuario que no es super admin
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    response = client.get('/admin-page', follow_redirects=True)
    assert response.status_code == 200
    assert '404'.encode('utf-8') in response.data 
    @pytest.fixture
    def app():
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()
            # Create a super admin user
            super_admin = Customer(
                username="superadmin",
                email="admin@tienda.com",
                password=generate_password_hash("password123"),
                role="super_admin"
            )
            db.session.add(super_admin)
            db.session.commit()
        yield app

    @pytest.fixture
    def client(app):
        return app.test_client()

    @pytest.fixture
    def login_super_admin(client):
        client.post('/auth/login', data={
            'email': 'admin@tienda.com',
            'password': 'password123'
        }, follow_redirects=True)

def test_admin_page_accessible_by_super_admin(client, login_super_admin):
    response = client.get('/admin-page', follow_redirects=True)
    assert response.status_code == 200
    assert b'Admin Panel' in response.data

def test_admin_page_redirects_to_404_if_not_super_admin(client):
    # Simulate login of a non-super admin user
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    response = client.get('/admin-page', follow_redirects=True)
    assert response.status_code == 200
    assert b'404' in response.data

def test_add_shop_items_requires_admin(client, login_super_admin):
    response = client.get('/add-shop-items', follow_redirects=True)
    assert response.status_code == 200
    assert b'Agregar Producto' in response.data

def test_shop_items_list(client, login_super_admin):
    response = client.get('/shop-items', follow_redirects=True)
    assert response.status_code == 200
    assert b'Lista de Productos' in response.data

def test_create_admin(client, login_super_admin):
    response = client.post('/create-admin', data={
    'username': 'newadmin',
    'email': 'newadmin@example.com',
        'password': 'password123',
        'role': 'admin',
        'force_password_change': False,
        'security_question1': 'Question 1',
        'security_answer1': 'Answer 1',
        'security_question2': 'Question 2',
        'security_answer2': 'Answer 2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Administrador creado exitosamente' in response.data

def test_update_user_role(client, login_super_admin):
    # Create a user to update
    with client.application.app_context():
        user = Customer(
            username="testuser",
            email="testuser@example.com",
            password=generate_password_hash("password123"),
            role="user"
        )
        db.session.add(user)
        db.session.commit()

    response = client.post(f'/update-user-role/{user.id}', data={
        'new_role': 'admin'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'actualizado exitosamente' in response.data

def test_delete_item(client, login_super_admin):
    # Create a product to delete
    with client.application.app_context():
        product = Product(
            product_name="Test Product",
            current_price=10.0,
            previous_price=15.0,
            in_stock=True,
            flash_sale=False,
            product_picture="test.jpg",
            created_by=1
        )
        db.session.add(product)
        db.session.commit()

    response = client.post(f'/delete-item/{product.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Producto "Test Product" eliminado exitosamente' in response.data

def test_view_orders(client, login_super_admin):
    response = client.get('/view-orders', follow_redirects=True)
    assert response.status_code == 200
    assert b'Lista de Pedidos' in response.data

def test_display_customers(client, login_super_admin):
    response = client.get('/customers', follow_redirects=True)
    assert response.status_code == 200
    assert b'Lista de Clientes' in response.data


