import pytest
from flask import Flask
from website import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        from website import db
        db.create_all()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_example(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_register_page(client):
    response = client.get('/auth/signup')
    assert response.status_code == 200

def test_logout_redirect(client):
    # Primero, simula un login
    client.post('/auth/login', data={
        'email': 'admin@tienda.com',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Iniciar sesión'.encode('utf-8') in response.data or 'login'.encode('utf-8') in response.data

def test_profile_requires_login(client):
    response = client.get('/profile', follow_redirects=True)
    # Debe redirigir a la página de login si no está autenticado
    assert 'Iniciar sesión'.encode('utf-8') in response.data or 'login'.encode('utf-8') in response.data