import pytest
from website import create_app, db
from website.models import Customer, Product, Category, Cart, Order
from flask_login import login_user

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def logged_in_client(client, app):
    with app.app_context():
        # Crear un usuario de prueba
        user = Customer(
            username='testuser',
            email='test@example.com',
            role='customer'
        )
        user.password = 'password123'
        db.session.add(user)
        db.session.commit()
        
        # Loguear al usuario usando el endpoint de login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        return client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_profile_page_requires_login(client):
    response = client.get('/profile')
    assert response.status_code == 302  # Redirección a login

def test_profile_page_with_login(logged_in_client):
    response = logged_in_client.get('/profile')
    assert response.status_code == 200

def test_admin_page_requires_admin(logged_in_client):
    response = logged_in_client.get('/admin')
    assert response.status_code == 302  # Redirección a home

def test_update_preferences_requires_login(client):
    response = client.post('/update_preferences', data={
        'email_notifications': 'on',
        'sms_notifications': 'on',
        'show_profile': 'on'
    })
    assert response.status_code == 302  # Redirección a login

def test_add_to_cart_requires_login(client):
    response = client.get('/add-to-cart/1')
    assert response.status_code == 302  # Redirect to login

def test_add_to_cart_with_login(logged_in_client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        # Crear un producto
        product = Product(
            product_name='Test Product',
            current_price=10.0,
            stock_quantity=5,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        # Agregar producto al carrito
        response = logged_in_client.get(f'/add-to-cart/{product.id}')
        assert response.status_code == 302  # Redirect back to referrer
        assert Cart.query.filter_by(product_id=product.id).first() is not None

def test_show_cart_requires_login(client):
    response = client.get('/cart')
    assert response.status_code == 302  # Redirect to login

def test_show_cart_with_login(logged_in_client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        # Crear un producto y agregarlo al carrito
        product = Product(
            product_name='Test Product',
            current_price=10.0,
            stock_quantity=5,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        cart_item = Cart(
            product_id=product.id,
            customer_id=1,
            quantity=1,
            total_price=10.0
        )
        db.session.add(cart_item)
        db.session.commit()
        response = logged_in_client.get('/cart')
        assert response.status_code == 200
        assert b'Test Product' in response.data

def test_place_order_requires_login(client):
    response = client.get('/place-order')
    assert response.status_code == 302  # Redirect to login

def test_place_order_with_items(logged_in_client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        # Crear un producto y agregarlo al carrito
        product = Product(
            product_name='Test Product',
            current_price=10.0,
            stock_quantity=5,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        cart_item = Cart(
            product_id=product.id,
            customer_id=1,
            quantity=1,
            total_price=10.0
        )
        db.session.add(cart_item)
        db.session.commit()
        response = logged_in_client.get('/place-order')
        assert response.status_code == 302  # Redirect to orders
        assert Order.query.filter_by(customer_id=1).first() is not None

def test_search_suggestions(client, app):
    with app.app_context():
        # Crear productos y categorías
        category = Category(name='Electronics')
        db.session.add(category)
        db.session.commit()
        product = Product(
            product_name='Laptop',
            description='A powerful laptop',
            current_price=999.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        response = client.get('/api/search/suggestions?q=laptop')
        assert response.status_code == 200
        assert b'laptop' in response.data or b'Laptop' in response.data

def test_search(client, app):
    with app.app_context():
        # Create a category first
        category = Category(name='Electronics')
        db.session.add(category)
        db.session.commit()

        # Create a product
        product = Product(
            product_name='Laptop',
            description='A powerful laptop',
            current_price=999.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()

        response = client.get('/search?q=laptop')
        assert response.status_code == 200
        assert b'Laptop' in response.data

def test_add_product_requires_admin(logged_in_client):
    response = logged_in_client.get('/add-product')
    assert response.status_code == 302  # Redirect to home

def test_list_products(client, app):
    with app.app_context():
        # Create a category first
        category = Category(name='Electronics')
        db.session.add(category)
        db.session.commit()

        # Create a product
        product = Product(
            product_name='Laptop',
            current_price=1000.0,
            stock_quantity=5,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        
        response = client.get('/list-products')
        assert response.status_code == 200
        assert b'Laptop' in response.data


