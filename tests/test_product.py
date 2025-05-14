import pytest
from flask import Flask
from website import create_app
from website.models import Category, Product

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        from website import db
        from website.models import Category, Product, db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_product_page(client):
    response = client.get('/product')
    assert response.status_code == 308 
def test_product_list(client):
    response = client.get('/product/')
    assert response.status_code == 200
    assert b'Products' in response.data  # Assuming the template contains the word "Products"
def test_add_product_get(client):
    response = client.get('/product/add')
    assert response.status_code == 200
    assert b'Add Product' in response.data  # Assuming the template contains the word "Add Product"
def test_add_product_post(client, app):
    with app.app_context():
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.commit()
        data = {
            'product_name': 'Test Product',
            'description': 'Test Description',
            'current_price': '10.99',
            'previous_price': '15.99',
            'in_stock': '100',
            'category_id': category.id,
            'discount': '5',
            'flash_sale': 'on'
        }
        response = client.post('/product/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Product added successfully!' in response.data
        assert Product.query.filter_by(product_name='Test Product').first() is not None
def test_edit_product_get(client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        product = Product(product_name="Test Product", description="Test", current_price=10.99, stock_quantity=10, category_id=category.id)
        db.session.add(product)
        db.session.commit()
        response = client.get(f'/product/edit/{product.id}')
        assert response.status_code == 200
        assert b'Edit Product' in response.data  # Assuming the template contains the word "Edit Product"
def test_edit_product_post(client, app):
    with app.app_context():
        # Create a category first
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        product = Product(
            product_name="Test Product",
            description="Test",
            current_price=10.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        data = {
            'product_name': 'Updated Product',
            'description': 'Updated Description',
            'current_price': '20.99',
            'previous_price': '25.99',
            'in_stock': '50',
            'discount': '10',
            'flash_sale': 'on'
        }
        response = client.post(f'/product/edit/{product.id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b'Product updated successfully!' in response.data
        updated_product = Product.query.get(product.id)
        assert updated_product.product_name == 'Updated Product'
def test_delete_product_get(client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        product = Product(product_name="Test Product", description="Test", current_price=10.99, stock_quantity=10, category_id=category.id)
        db.session.add(product)
        db.session.commit()
        response = client.get(f'/product/delete/{product.id}')
        assert response.status_code == 200
        assert b'Delete Product' in response.data  # Assuming the template contains the word "Delete Product"
def test_delete_product_post(client, app):
    with app.app_context():
        # Crear una categoría primero
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()
        product = Product(product_name="Test Product", description="Test", current_price=10.99, stock_quantity=10, category_id=category.id)
        db.session.add(product)
        db.session.commit()
        response = client.post(f'/product/delete/{product.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b'ha sido eliminado exitosamente' in response.data  # Assuming the flash message contains this text
        assert Product.query.get(product.id) is None
def test_product_detail(client, app):
    with app.app_context():
        # Create a category first
        category = Category(name='Test Category')
        db.session.add(category)
        db.session.commit()

        product = Product(
            product_name="Test Product",
            description="Test",
            current_price=10.99,
            stock_quantity=10,
            category_id=category.id
        )
        db.session.add(product)
        db.session.commit()
        response = client.get(f'/product/detail/{product.id}')
        assert response.status_code == 200
        assert b'Test Product' in response.data  # Assuming the template displays the product name
def test_category_products(client, app):
    with app.app_context():
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.commit()
        product = Product(product_name="Test Product", description="Test", current_price=10.99, stock_quantity=10, category_id=category.id)
        db.session.add(product)
        db.session.commit()
        response = client.get(f'/product/category/{category.id}')
        assert response.status_code == 200
        assert b'Test Product' in response.data  # Assuming the template displays the product name