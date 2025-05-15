import pytest
from website.models import Customer, Product, Category, Order, db
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
def super_admin(app):
    with app.app_context():
        admin = Customer(
            email='superadmin@test.com',
            username='superadmin'
        )
        admin.password = 'admin123'
        admin.set_super_admin(True)
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def login_super_admin(client, super_admin):
    client.post('/auth/login', data={
        'email': 'superadmin@test.com',
        'password': 'admin123'
    })
    return client

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

def test_admin_page_accessible_by_super_admin(client, test_user):
    """Test de acceso a la página de administración por super admin."""
    # Primero hacer login como super admin
    test_user.role = 'super_admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Panel de Administraci\xc3\xb3n' in response.data

def test_add_shop_items_requires_admin(client, test_user):
    """Test de que agregar productos requiere ser admin."""
    # Primero hacer login como usuario normal
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/add-product', follow_redirects=True)
    assert response.status_code == 200
    assert b'No tienes permisos para acceder a esta p\xc3\xa1gina' in response.data

def test_shop_items_list(client, test_user):
    """Test de lista de productos."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/list-products')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Productos' in response.data

def test_create_admin(client, test_user):
    """Test de creación de administrador."""
    # Primero hacer login como super admin
    test_user.role = 'super_admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/make_admin/2', follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario actualizado a administrador' in response.data

def test_update_user_role(client, test_user):
    """Test de actualización de rol de usuario."""
    # Primero hacer login como super admin
    test_user.role = 'super_admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/update_user_role/2', data={
        'role': 'admin'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Rol de usuario actualizado' in response.data

def test_delete_item(client, test_user, test_product):
    """Test de eliminación de producto."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get(f'/delete-item/{test_product.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Producto eliminado exitosamente' in response.data

def test_view_orders(client, test_user):
    """Test de vista de pedidos."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/orders')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Pedidos' in response.data

def test_display_customers(client, test_user):
    """Test de visualización de clientes."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Usuarios' in response.data

def test_admin_dashboard_requires_admin(client, test_user):
    """Test de que el dashboard requiere ser admin."""
    # Primero hacer login como usuario normal
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    assert b'No tienes permisos para acceder a esta p\xc3\xa1gina' in response.data

def test_admin_dashboard_with_admin(client, test_user):
    """Test de dashboard con usuario admin."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Panel de Administraci\xc3\xb3n' in response.data

def test_admin_users_list(client, test_user):
    """Test de lista de usuarios."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Usuarios' in response.data

def test_admin_create_user(client, test_user):
    """Test de creación de usuario."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/admin/add_user', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'testpassword123',
        'role': 'customer'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario creado exitosamente' in response.data

def test_admin_edit_user(client, test_user):
    """Test de edición de usuario."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/admin/edit_user/2', data={
        'username': 'updateduser',
        'email': 'updated@example.com',
        'role': 'customer'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario actualizado exitosamente' in response.data

def test_admin_delete_user(client, test_user):
    """Test de eliminación de usuario."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/admin/delete_user/2', follow_redirects=True)
    assert response.status_code == 200
    assert b'Usuario eliminado exitosamente' in response.data

def test_admin_products_list(client, test_user):
    """Test de lista de productos."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/products')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Productos' in response.data

def test_admin_categories_list(client, test_user):
    """Test de lista de categorías."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/categories')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Categor\xc3\xadas' in response.data

def test_admin_create_category(client, test_user):
    """Test de creación de categoría."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/admin/add_category', data={
        'name': 'New Category',
        'description': 'New Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Categor\xc3\xada creada exitosamente' in response.data

def test_admin_edit_category(client, test_user, test_category):
    """Test de edición de categoría."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/admin/edit_category/{test_category.id}', data={
        'name': 'Updated Category',
        'description': 'Updated Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Categor\xc3\xada actualizada exitosamente' in response.data

def test_admin_delete_category(client, test_user, test_category):
    """Test de eliminación de categoría."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/admin/delete_category/{test_category.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Categor\xc3\xada eliminada exitosamente' in response.data

def test_admin_orders_list(client, test_user):
    """Test de lista de pedidos."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/orders')
    assert response.status_code == 200
    assert b'Gesti\xc3\xb3n de Pedidos' in response.data

def test_admin_order_detail(client, test_user, test_order):
    """Test de detalle de pedido."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get(f'/admin/order/{test_order.id}')
    assert response.status_code == 200
    assert b'Detalles del Pedido' in response.data

def test_admin_update_order_status(client, test_user, test_order):
    """Test de actualización de estado de pedido."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post(f'/admin/order/{test_order.id}/update_status', data={
        'status': 'shipped'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Estado del pedido actualizado exitosamente' in response.data

def test_admin_dashboard_stats(client, test_user):
    """Test de estadísticas del dashboard."""
    # Primero hacer login como admin
    test_user.role = 'admin'
    db.session.commit()
    
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/admin/stats')
    assert response.status_code == 200
    assert b'Estad\xc3\xadsticas' in response.data


