import os
import pytest
from website import create_app, generate_secure_password, db
from flask import Flask


def test_generate_secure_password_length():
    password = generate_secure_password(16)
    assert len(password) == 16
    assert any(c.islower() for c in password)
    assert any(c.isupper() for c in password)
    assert any(c.isdigit() for c in password)
    assert any(not c.isalnum() for c in password)

def test_generate_secure_password_default():
    password = generate_secure_password()
    assert len(password) == 12

def test_create_app_env(monkeypatch):
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('MAIL_USERNAME', 'test@mail.com')
    monkeypatch.setenv('MAIL_PASSWORD', 'testpass')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', 'noreply@test.com')
    app = create_app()
    assert isinstance(app, Flask)
    assert app.config['SECRET_KEY'] == 'test-secret-key'
    assert app.config['MAIL_USERNAME'] == 'test@mail.com'
    assert app.config['MAIL_PASSWORD'] == 'testpass'
    assert app.config['MAIL_DEFAULT_SENDER'] == 'noreply@test.com'

def test_create_app_database(monkeypatch, tmp_path):
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('MAIL_USERNAME', 'test@mail.com')
    monkeypatch.setenv('MAIL_PASSWORD', 'testpass')
    monkeypatch.setenv('MAIL_DEFAULT_SENDER', 'noreply@test.com')
    # Usar una carpeta temporal para la instancia
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Verificar que las tablas existen
        inspector = db.inspect(db.engine)
        assert 'customer' in inspector.get_table_names()
        assert 'product' in inspector.get_table_names()
        assert 'order' in inspector.get_table_names()
        assert 'category' in inspector.get_table_names() 