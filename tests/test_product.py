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

def test_product_page(client):
    response = client.get('/product')
    assert response.status_code == 308 