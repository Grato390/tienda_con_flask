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

def test_add_product_get(logged_in_admin):
    response = logged_in_admin.get('/product/add')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Agregar Producto' in soup.get_text()

def test_add_product_post(logged_in_admin, app):
    with app.app_context():
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        response = logged_in_admin.post('/product/add', data={
            'product_name': 'Test Product',
            'description': 'Test Description',
            'current_price': 10.0,
            'stock_quantity': 5,
            'category_id': category.id
        }, follow_redirects=True)

        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        assert 'Producto agregado exitosamente' in soup.get_text()

def test_edit_product_get(client, test_user, test_product):
    """Test de edición de producto (GET)."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get(f'/product/edit/{test_product.id}')
    assert response.status_code == 200
    assert 'Editar Producto'.encode('utf-8') in response.data

def test_edit_product_post(client, test_user, test_product):
    """Test de edición de producto (POST)."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/product/edit/{test_product.id}', data={
        'product_name': 'Updated Product',
        'description': 'Updated Description',
        'current_price': 29.99,
        'stock_quantity': 10,
        'category_id': test_product.category_id
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Producto actualizado exitosamente'.encode('utf-8') in response.data

def test_delete_product_get(client, test_user, test_product):
    """Test de eliminación de producto (GET)."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get(f'/product/delete/{test_product.id}')
    assert response.status_code == 200
    assert 'Confirmar eliminación'.encode('utf-8') in response.data

def test_delete_product_post(client, test_user, test_product):
    """Test de eliminación de producto (POST)."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/product/delete/{test_product.id}', follow_redirects=True)
    assert response.status_code == 200
    assert 'Producto eliminado exitosamente'.encode('utf-8') in response.data

def test_product_detail(client, test_product):
    """Test de detalle de producto."""
    response = client.get(f'/product/detail/{test_product.id}')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

def test_category_products(client, test_category, test_product):
    """Test de productos por categoría."""
    response = client.get(f'/category/{test_category.id}/products')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

def test_product_list_page(client):
    """Test de la página de lista de productos."""
    response = client.get('/list-products')
    assert response.status_code == 200
    assert b'Productos' in response.data

def test_product_detail_page(client, test_product):
    """Test de la página de detalle de producto."""
    response = client.get(f'/product/detail/{test_product.id}')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

def test_product_create_page(client, test_user):
    """Test de página de creación de producto."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/product/create')
    assert response.status_code == 200
    assert 'Crear Producto'.encode('utf-8') in response.data

def test_product_create(client, test_user, test_category):
    """Test de creación de producto."""
    # Primero hacer login como admin
    test_user.set_admin(True)
    db.session.commit()
    
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/product/create', data={
        'product_name': 'New Product',
        'description': 'New Description',
        'current_price': 19.99,
        'stock_quantity': 5,
        'category_id': test_category.id
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Producto agregado exitosamente'.encode('utf-8') in response.data

def test_product_edit_page(client, test_user, test_product):
    """Test de la página de edición de producto."""
    # Primero hacer login como admin
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get(f'/product/edit/{test_product.id}')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

def test_product_edit(client, test_user, test_product):
    """Test de edición de producto."""
    # Primero hacer login como admin
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/product/edit/{test_product.id}', data={
        'product_name': 'Updated Product',
        'description': 'Updated Description',
        'current_price': 15.0,
        'stock_quantity': 8,
        'category_id': test_product.category_id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Producto actualizado exitosamente' in response.data

def test_product_delete(client, test_user, test_product):
    """Test de eliminación de producto."""
    # Primero hacer login como admin
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/product/delete/{test_product.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Producto eliminado exitosamente' in response.data

def test_product_search(client, test_product):
    """Test de búsqueda de productos."""
    response = client.get('/search?q=Test')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

def test_product_filter_by_category(client, test_product):
    """Test de filtrado de productos por categoría."""
    response = client.get(f'/category/{test_product.category_id}/products')
    assert response.status_code == 200
    assert test_product.product_name.encode('utf-8') in response.data

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

def test_product_out_of_stock(client, test_product):
    """Test de producto sin stock."""
    test_product.stock_quantity = 0
    test_product.in_stock = False
    db.session.commit()
    
    response = client.get(f'/product/detail/{test_product.id}')
    assert response.status_code == 200
    assert b'Agotado' in response.data

def test_product_with_discount(client, test_product):
    """Test de producto con descuento."""
    test_product.previous_price = 15.0
    test_product.current_price = 10.0
    db.session.commit()
    
    response = client.get(f'/product/detail/{test_product.id}')
    assert response.status_code == 200
    assert b'OFF' in response.data