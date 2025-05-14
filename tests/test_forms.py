import pytest
from flask import Flask
from website import create_app
from website.forms import SignUpForm, LoginForm, EditProfileForm

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

def test_signup_form_validation(app):
    with app.test_request_context():
        # Prueba con datos válidos
        form = SignUpForm(
            email='test@example.com',
            username='testuser',
            password1='Password123!',
            password2='Password123!'
        )
        assert form.validate() is True

        # Prueba con contraseña débil
        form = SignUpForm(
            email='test@example.com',
            username='testuser',
            password1='weak',
            password2='weak'
        )
        assert form.validate() is False
        assert 'La contraseña debe tener al menos 8 caracteres' in str(form.password1.errors)

        # Prueba con contraseñas que no coinciden
        form = SignUpForm(
            email='test@example.com',
            username='testuser',
            password1='Password123!',
            password2='Different123!'
        )
        assert form.validate() is False
        assert 'Field must be equal to password1' in str(form.password2.errors)

def test_login_form_validation(app):
    with app.test_request_context():
        # Prueba con datos válidos
        form = LoginForm(
            email='test@example.com',
            password='Password123!'
        )
        assert form.validate() is True

        # Prueba con email inválido
        form = LoginForm(
            email='invalid-email',
            password='Password123!'
        )
        assert form.validate() is False
        assert 'Invalid email address' in str(form.email.errors)

def test_edit_profile_form_validation(app):
    with app.test_request_context():
        # Prueba con datos válidos
        form = EditProfileForm(
            username='newusername',
            email='new@example.com',
            phone_number='1234567890',
            address='New Address',
            security_key='Password123!',
            new_password='NewPassword123!',
            confirm_password='NewPassword123!'
        )
        assert form.validate() is True

        # Prueba con email inválido
        form = EditProfileForm(
            username='newusername',
            email='invalid-email',
            phone_number='1234567890',
            address='New Address',
            security_key='Password123!',
            new_password='NewPassword123!',
            confirm_password='NewPassword123!'
        )
        assert form.validate() is False
        assert 'Invalid email address' in str(form.email.errors) 