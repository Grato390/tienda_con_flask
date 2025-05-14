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

def test_admin_page_redirects_to_404_if_not_super_admin(client):
    # Simula un login de un usuario que no es super admin
    client.post('/auth/login', data={
        'email': 'user@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    response = client.get('/admin-page', follow_redirects=True)
    assert response.status_code == 200
    assert '404'.encode('utf-8') in response.data 