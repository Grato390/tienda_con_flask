import pytest
from website import create_app, db
from website.models import Customer, Product, Category, Cart, Order
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='function')
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

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def test_user(app):
    """Fixture para crear un usuario de prueba con permisos de administrador."""
    user = Customer(
        username='testuser',
        email='test@example.com',
        password=generate_password_hash('testpassword123')
    )
    user.set_admin(True)  # Usar el nuevo método para establecer el rol de admin
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def test_admin(app):
    admin = Customer(
        email='admin@example.com',
        username='admin',
        password=generate_password_hash('adminpassword123')
    )
    admin.set_admin(True)  # Usar el nuevo método para establecer el rol de admin
    db.session.add(admin)
    db.session.commit()
    return admin

@pytest.fixture(scope='function')
def test_category(app):
    category = Category(name='Test Category')
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture(scope='function')
def test_product(app, test_category):
    """Fixture para crear un producto de prueba."""
    product = Product(
        product_name='Test Product',
        description='Test Description',
        current_price=100.00,
        previous_price=120.00,  # Agregamos precio anterior para pruebas de descuento
        stock_quantity=10,
        in_stock=True,
        category_id=test_category.id,
        product_picture=None,  # Imagen opcional
        flash_sale=False
    )
    db.session.add(product)
    db.session.commit()
    return product

@pytest.fixture(scope='function')
def test_cart(app, test_user, test_product):
    cart = Cart(
        customer_id=test_user.id,
        product_id=test_product.id,
        quantity=1,
        total_price=test_product.current_price
    )
    db.session.add(cart)
    db.session.commit()
    return cart

@pytest.fixture(scope='function')
def test_order(app, test_user, test_product):
    order = Order(
        customer_id=test_user.id,
        status='pending',
        total=test_product.current_price,
        shipping_address='Test Address'
    )
    db.session.add(order)
    db.session.commit()
    return order 