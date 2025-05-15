import pytest
from website.models import Customer, Product, Category, Cart, Order, db
from bs4 import BeautifulSoup
from flask import url_for
from flask_login import current_user

@pytest.fixture
def app():
    from website import create_app
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
def logged_in_client(client, app):
    with app.app_context():
        user = Customer(
            email='test@example.com',
            username='testuser'
        )
        user.password = 'password123'
        user.set_admin(True)
        db.session.add(user)
        db.session.commit()

    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    return client

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

def test_home_page(client):
    """Test de la página principal."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Tienda Online' in response.data

def test_about_page(client):
    """Test de la página About."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b'Sobre Nosotros' in response.data

def test_cart_page_requires_login(client):
    """Test de que el carrito requiere inicio de sesión."""
    response = client.get('/cart', follow_redirects=True)
    assert response.status_code == 200
    assert 'Por favor inicia sesión para acceder a esta página'.encode('utf-8') in response.data


def test_add_to_cart_requires_login(client, test_product):
    """Test de que agregar al carrito requiere inicio de sesión."""
    response = client.get(f'/add-to-cart/{test_product.id}', follow_redirects=True)
    assert response.status_code == 200
    assert 'Por favor inicia sesión para acceder a esta página'.encode('utf-8') in response.data


def test_checkout_requires_login(client):
    """Test de que el checkout requiere inicio de sesión."""
    response = client.get('/place-order', follow_redirects=True)
    assert response.status_code == 200
    assert 'Por favor inicia sesión para acceder a esta página'.encode('utf-8') in response.data


def test_order_history_requires_login(client):
    """Test de que el historial de pedidos requiere inicio de sesión."""
    response = client.get('/orders', follow_redirects=True)
    assert response.status_code == 200
    assert 'Por favor inicia sesión para acceder a esta página'.encode('utf-8') in response.data


def test_search_page(client):
    """Test de la página de búsqueda."""
    response = client.get('/search')
    assert response.status_code == 200
    assert b'Buscar productos' in response.data

def test_search_with_query(client, test_product):
    response = client.get(f'/search?q={test_product.product_name}')
    assert response.status_code == 200
    assert test_product.product_name.encode() in response.data

def test_category_list_page(client):
    """Test de la página de lista de categorías."""
    response = client.get('/categories')
    assert response.status_code == 200
    assert 'Categorías'.encode('utf-8') in response.data

def test_category_products_page(client, test_category):
    """Test de la página de productos por categoría."""
    response = client.get(f'/category/{test_category.id}/products')
    assert response.status_code == 200
    assert test_category.name.encode() in response.data

def test_user_profile_requires_login(client):
    """Test de que el perfil requiere inicio de sesión."""
    response = client.get('/profile', follow_redirects=True)
    assert response.status_code == 200
    assert 'Por favor inicia sesión para acceder a esta página'.encode('utf-8') in response.data


