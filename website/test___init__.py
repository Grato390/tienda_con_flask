import os
import pytest
import string
from flask import Flask
from website import create_app, db, generate_secure_password, create_super_admin
from website.models import Customer

@pytest.fixture
def app():
    """Fixture to create a Flask app instance for testing."""
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['ADMIN_SECURITY_KEY'] = 'test-admin-key'
    os.environ['SUPER_ADMIN_PASSWORD'] = 'test-super-admin-password'
    os.environ['MAIL_USERNAME'] = 'test@mail.com'
    os.environ['MAIL_PASSWORD'] = 'test-password'
    os.environ['MAIL_DEFAULT_SENDER'] = 'test-sender@mail.com'

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Fixture to create a test client."""
    return app.test_client()

def test_generate_secure_password():
    """Test the generate_secure_password function."""
    password = generate_secure_password(16)
    assert len(password) == 16
    assert any(char.isdigit() for char in password)
    assert any(char.isalpha() for char in password)
    assert any(char in string.punctuation for char in password)

def test_create_super_admin(app):
    """Test the create_super_admin function."""

    with app.app_context():
        create_super_admin()
        super_admin = Customer.query.filter_by(role='super_admin').first()
        assert super_admin is not None
        assert super_admin.email == 'admin@tienda.com'
        assert super_admin.username == 'super_admin'
        assert super_admin.role == 'super_admin'

def test_create_app(client):
    """Test the create_app function."""
    response = client.get('/')
    assert response.status_code in [200, 404]  # Depends on whether the root route is defined

def test_media_route(client):
    """Test the media route."""
    response = client.get('/media/testfile.txt')
    assert response.status_code == 404  # File does not exist in test environment

def test_error_handlers(client):
    """Test the error handlers."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404