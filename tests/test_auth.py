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

def test_login_page(client):
    """Test de la página de inicio de sesión."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Iniciar sesi\xc3\xb3n' in response.data

def test_sign_up_page(client):
    """Test de la página de registro."""
    response = client.get('/sign-up')
    assert response.status_code == 200
    assert b'Registrarse' in response.data

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

def test_sign_up_success(client):
    """Test de registro exitoso."""
    response = client.post('/sign-up', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password1': 'testpassword123',
        'password2': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Cuenta creada exitosamente' in response.data

def test_sign_up_existing_email(client, test_user):
    """Test de registro con email existente."""
    response = client.post('/sign-up', data={
        'username': 'testuser2',
        'email': test_user.email,
        'password1': 'testpassword123',
        'password2': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'El email ya est\xc3\xa1 registrado' in response.data

def test_login_success(client, test_user):
    """Test de inicio de sesión exitoso."""
    response = client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Inicio de sesi\xc3\xb3n exitoso' in response.data

def test_login_invalid_password(client, test_user):
    """Test de inicio de sesión con contraseña incorrecta."""
    response = client.post('/login', data={
        'email': test_user.email,
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Contrase\xc3\xb1a incorrecta' in response.data

def test_login_nonexistent_email(client):
    """Test de inicio de sesión con email inexistente."""
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'El email no existe' in response.data

def test_logout(client, test_user):
    """Test de cierre de sesión."""
    # Primero hacer login
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Iniciar sesi\xc3\xb3n' in response.data

def test_profile_with_login(client, test_user):
    """Test de perfil con usuario logueado."""
    # Primero hacer login
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/profile')
    assert response.status_code == 200
    assert test_user.username.encode() in response.data

def test_edit_profile(client, test_user):
    """Test de edición de perfil."""
    # Primero hacer login
    client.post('/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/update_profile', data={
        'username': 'updatedusername',
        'email': test_user.email,
        'phone_number': '123456789',
        'address': 'Test Address'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Perfil actualizado exitosamente' in response.data

def test_forgot_password(client):
    """Test de recuperación de contraseña."""
    response = client.post('/forgot-password', data={
        'email': 'test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Se ha enviado un correo con instrucciones' in response.data

def test_register_user(client, app):
    response = client.post('/auth/register', data={
        'email': 'newuser@example.com',
        'username': 'newuser',
        'password1': 'testpassword123',
        'password2': 'testpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        user = Customer.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.username == 'newuser'

def test_register_duplicate_email(client, test_user):
    response = client.post('/auth/register', data={
        'email': test_user.email,
        'username': 'differentuser',
        'password1': 'testpassword123',
        'password2': 'testpassword123'
    })
    assert b'Email already exists' in response.data

def test_login_wrong_password(client, test_user):
    response = client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'wrongpassword'
    })
    assert b'Incorrect password' in response.data

def test_password_reset_request_page(client):
    response = client.get('/auth/reset-password-request')
    assert response.status_code == 200
    assert b'Reset Password' in response.data

def test_password_reset_request(client, test_user):
    response = client.post('/auth/reset-password-request', data={
        'email': test_user.email
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Check your email for the instructions to reset your password' in response.data

def test_password_reset_request_nonexistent_email(client):
    response = client.post('/auth/reset-password-request', data={
        'email': 'nonexistent@example.com'
    })
    assert b'Email does not exist' in response.data

def test_change_password_page(client, test_user):
    # Primero hacer login
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.get('/auth/change-password')
    assert response.status_code == 200
    assert b'Change Password' in response.data

def test_change_password(client, test_user):
    # Primero hacer login
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/auth/change-password', data={
        'current_password': 'testpassword123',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Password changed successfully' in response.data

def test_change_password_wrong_current(client, test_user):
    # Primero hacer login
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/auth/change-password', data={
        'current_password': 'wrongpassword',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123'
    })
    assert b'Current password is incorrect' in response.data

def test_change_password_mismatch(client, test_user):
    # Primero hacer login
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    
    response = client.post('/auth/change-password', data={
        'current_password': 'testpassword123',
        'new_password': 'newpassword123',
        'confirm_password': 'differentpassword'
    })
    assert b'Passwords do not match' in response.data




