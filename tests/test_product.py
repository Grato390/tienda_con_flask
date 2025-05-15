import pytest
from flask import Flask, url_for
from website import create_app
from website.models import Product, Category, Customer, db, Cart
from bs4 import BeautifulSoup
from flask_login import current_user

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

@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = Customer(
            email='admin@test.com',
            username='admin'
        )
        admin.password = 'admin123'
        admin.set_admin(True)
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def logged_in_admin(client, admin_user):
    client.post('/auth/login', data={
        'email': 'admin@test.com',
        'password': 'admin123'
    })
    return client

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

@pytest.fixture
def test_product(db_session):
    """Fixture para crear un producto de prueba."""
    category = Category(name='Test Category', description='Test Description')
    db_session.add(category)
    db_session.commit()
    
    product = Product(
        product_name='Test Product',
        description='Test Description',
        current_price = 10.0,
        previous_price = 15.0,
        in_stock=True,
        stock_quantity=5,
        flash_sale=False,
        product_picture='test.jpg',
        category_id=category.id,
        created_at='2023-10-01 00:00:00',
        updated_at='2023-10-01 00:00:00',
        created_by=1 # Assuming user with ID 1 exists  
    )
    db_session.add(product)
    db_session.commit()
    return product

def test_product_page(client):
    response = client.get('/product')
    assert response.status_code == 308 

def test_product_list(client, app):
    with app.app_context():
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        product = Product(
            product_name='Test Product',
            description='Test Description',
            current_price=10.0,
            stock_quantity=5,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()

        response = client.get('/product/')
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        assert 'Test Product' in soup.get_text()

def test_product_list_page(client):
    """Test de la página de lista de productos."""
    response = client.get('/list-products')
    assert response.status_code == 200
    assert b'Productos' in response.data

def test_product_filter_by_price(client):
    """Test product filtering by price."""
    response = client.get('/list-products?min_price=10&max_price=100')
    assert response.status_code == 200

def test_product_sort_by_price(client):
    """Test product sorting by price."""
    response = client.get('/list-products?sort=price_asc')
    assert response.status_code == 200

def test_product_sort_by_name(client):
    """Test product sorting by name."""
    response = client.get('/list-products?sort=name_asc')
    assert response.status_code == 200


