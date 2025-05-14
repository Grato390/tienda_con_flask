import pytest
from flask import Flask
from website import create_app
from bs4 import BeautifulSoup

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
def test_sign_up_page(client):
    response = client.get('/auth/sign-up')
    assert response.status_code == 200
    assert b'Registrarse' in response.data

def test_sign_up_success(client):
    response = client.post('/auth/sign-up', data={
        'email': 'testuser@example.com',
        'username': 'testuser',
        'password1': 'Password123',
        'password2': 'Password123'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Analiza el HTML de la respuesta
    soup = BeautifulSoup(response.data, 'html.parser')
    assert '¡Cuenta creada exitosamente!' in soup.get_text()

def test_sign_up_existing_email(client):
    client.post('/auth/sign-up', data={
        'email': 'existing@example.com',
        'username': 'existinguser',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    response = client.post('/auth/sign-up', data={
        'email': 'existing@example.com',
        'username': 'newuser',
        'password1': 'Password123',
        'password2': 'Password123'
    }, follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'El email ya existe.' in soup.get_text()

def test_login_success(client):
    client.post('/auth/sign-up', data={
        'email': 'loginuser@example.com',
        'username': 'loginuser',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    response = client.post('/auth/login', data={
        'email': 'loginuser@example.com',
        'password': 'Password123'
    }, follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert '¡Inicio de sesión exitoso!' in soup.get_text()

def test_login_invalid_password(client):
    client.post('/auth/sign-up', data={
        'email': 'invalidpass@example.com',
        'username': 'invalidpass',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    response = client.post('/auth/login', data={
        'email': 'invalidpass@example.com',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Contraseña incorrecta.' in soup.get_text()

def test_login_nonexistent_email(client):
    response = client.post('/auth/login', data={
        'email': 'nonexistent@example.com',
        'password': 'Password123'
    }, follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'El email no está registrado.' in soup.get_text()

def test_logout(client):
    client.post('/auth-sign-up', data={
        'email': 'logoutuser@example.com',
        'username': 'logoutuser',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    client.post('/auth/login', data={
        'email': 'logoutuser@example.com',
        'password': 'Password123'
    })
    response = client.get('/auth/logout', follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Iniciar sesión' in soup.get_text()

def test_forgot_password(client):
    client.post('/auth/sign-up', data={
        'email': 'forgotpass@example.com',
        'username': 'forgotpass',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    response = client.post('/auth/forgot-password', data={
        'email': 'forgotpass@example.com'
    }, follow_redirects=True)
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Se ha enviado un correo con instrucciones' in soup.get_text()

def test_forgot_password_invalid_email(client):
    response = client.post('/auth/forgot-password', data={
        'email': 'invalid@example.com'
    }, follow_redirects=True)
    assert 'No se encontró ninguna cuenta con ese correo electrónico.'.encode('utf-8') in response.data

def test_forgot_password(client):
    client.post('/auth/sign-up', data={
        'email': 'forgotpass@example.com',
        'username': 'forgotpass',
        'password1': 'Password123',
        'password2': 'Password123'
    })
    response = client.post('/auth/forgot-password', data={
        'email': 'forgotpass@example.com'
    }, follow_redirects=True)

    # Analiza el HTML de la respuesta
    soup = BeautifulSoup(response.data, 'html.parser')
    assert 'Se ha enviado un correo con instrucciones' in soup.get_text()




