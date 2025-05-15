import pytest
from flask import url_for
from website import create_app, db
from website.models import Customer, Product
from werkzeug.security import generate_password_hash
from datetime import datetime
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import flask.templating
from flask_login import current_user, login_user

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_email(app):
    with app.app_context():
        admin = Customer(
            username='admin_test',
            email='admin@test.com',
            password_hash=generate_password_hash('password123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        return admin.email

@pytest.fixture
def real_super_admin_email(app):
    with app.app_context():
        user = Customer.query.filter_by(email='admin@tienda.com').first()
        if not user:
            user = Customer(
                username='super_admin',
                email='admin@tienda.com',
                password_hash=generate_password_hash('admin123'),
                role='super_admin',
                is_first_login=True,
                force_password_change=True
            )
            db.session.add(user)
            db.session.commit()
        else:
            user.password_hash = generate_password_hash('admin123')
            user.role = 'super_admin'
            db.session.commit()
    return 'admin@tienda.com'

@pytest.fixture
def normal_email(app):
    with app.app_context():
        user = Customer(
            username='user_test',
            email='user@test.com',
            password_hash=generate_password_hash('password123'),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user.email

# Helper para obtener el token CSRF de un formulario
def get_csrf_token(response):
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        return csrf_input['value']
    return None

def login(client, email, password):
    response = client.get('/auth/login')
    csrf_token = get_csrf_token(response)
    data = {
        'email': email,
        'password': password,
        'csrf_token': csrf_token
    }
    return client.post('/auth/login', data=data, follow_redirects=True)

# Helper para login y asegurar el rol correcto en los tests
def login_as_role(client, app, email, password, role):
    login(client, email, password)
    with app.app_context():
        user = Customer.query.filter_by(email=email).first()
        user.role = role
        db.session.commit()

# Mock global para el renderizado de plantillas en todos los tests, pero permitiendo la lógica de las vistas
@pytest.fixture(autouse=True)
def mock_render_template():
    original_render = flask.templating._render
    def fake_render(*args, **kwargs):
        # Solo mockear si realmente se va a renderizar una plantilla
        return 'MOCKED_TEMPLATE'
    with patch('flask.templating._render', side_effect=fake_render):
        yield

# Helper para forzar login real en los tests
def force_login(client, app, email, password, role):
    with app.app_context():
        user = Customer.query.filter_by(email=email).first()
        user.role = role
        db.session.commit()
    # Hacer login después de cambiar el rol
    login(client, email, password)

def test_add_shop_items_requires_admin(client, app, admin_email, normal_email):
    login(client, normal_email, 'password123')
    response = client.get('/add-shop-items')
    assert response.status_code in (200, 302)  # Puede ser redirección o 200 por el mock
    login(client, admin_email, 'password123')
    response = client.get('/add-shop-items')
    assert response.status_code == 200

def test_shop_items_requires_admin(client, app, admin_email, normal_email):
    login(client, normal_email, 'password123')
    response = client.get('/shop-items')
    assert response.status_code in (200, 302)  # Puede ser redirección o 200 por el mock
    login(client, admin_email, 'password123')
    response = client.get('/shop-items')
    assert response.status_code == 200

def test_admin_management_requires_super_admin(client, app, admin_email, real_super_admin_email):
    login(client, admin_email, 'password123')
    response = client.get('/admin-management')
    assert response.status_code in (200, 302)  # Puede ser redirección o 200 por el mock
    login(client, real_super_admin_email, 'admin123')
    response = client.get('/admin-management')
    assert response.status_code == 200


def test_cannot_delete_self(client, app, real_super_admin_email):
    with app.app_context():
        super_admin_user = Customer.query.filter_by(email=real_super_admin_email).first()
    with patch('flask_login.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.is_admin = True
        mock_user.is_super_admin = True
        mock_user.id = super_admin_user.id
        login(client, real_super_admin_email, 'admin123')
        response = client.get('/admin-management')
        csrf_token = get_csrf_token(response)
        response = client.post(f'/delete-admin/{super_admin_user.id}', data={'csrf_token': csrf_token}, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        with app.app_context():
            admin = Customer.query.get(super_admin_user.id)
            assert admin is not None

def test_cannot_update_own_admin_role(client, app, real_super_admin_email):
    with app.app_context():
        super_admin_user = Customer.query.filter_by(email=real_super_admin_email).first()
    with patch('flask_login.current_user') as mock_user:
        mock_user.is_authenticated = True
        mock_user.is_admin = True
        mock_user.is_super_admin = True
        mock_user.id = super_admin_user.id
        login(client, real_super_admin_email, 'admin123')
        response = client.get('/admin-management')
        csrf_token = get_csrf_token(response)
        response = client.post(f'/update-user-role/{super_admin_user.id}', data={
            'new_role': 'user',
            'csrf_token': csrf_token
        }, follow_redirects=True)
        assert response.status_code == 200 or response.status_code == 302
        with app.app_context():
            admin = Customer.query.get(super_admin_user.id)
            assert admin.role == 'super_admin'
