import pytest
from flask import Flask, url_for
from website import create_app
from bs4 import BeautifulSoup
from website.models import Customer, db
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

@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

def test_example(client):
    response = client.get('/')
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
    """Test de que el perfil requiere inicio de sesión."""
    response = client.get('/profile', follow_redirects=True)
    assert response.status_code == 200
    assert b'Por favor inicia sesi\xc3\xb3n para acceder a esta p\xc3\xa1gina' in response.data

