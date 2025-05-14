import pytest
from website import create_app, db
from website.models import Customer, Product, Category
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

