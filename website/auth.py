from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from .forms import LoginForm, SignUpForm, PasswordChangeForm, ResetPasswordForm, EditProfileForm
from .models import Customer
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import re
from datetime import datetime, timedelta
import os
import random
import string


auth = Blueprint('auth', __name__)
# Constantes para endpoints
HOME_ENDPOINT = 'views.home'
LOGIN_ENDPOINT = 'auth.login'

# Constantes para plantillas
LOGIN_TEMPLATE = 'auth/login.html'
# Configuración de Flask-Mail
mail = Mail()
serializer = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'your-secret-key'))
import random
import string

def generate_secure_password(length):
    if length < 4:
        raise ValueError("La longitud de la contraseña debe ser al menos 4 para incluir todos los tipos de caracteres.")

    # Asegúrate de incluir al menos un carácter de cada tipo
    lower = random.choice(string.ascii_lowercase)
    upper = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice(string.punctuation)

    # Rellena el resto de la contraseña con caracteres aleatorios
    remaining_length = length - 4
    all_characters = string.ascii_letters + string.digits + string.punctuation
    remaining = ''.join(random.choices(all_characters, k=remaining_length))

    # Mezcla los caracteres para evitar patrones predecibles
    password = list(lower + upper + digit + special + remaining)
    random.shuffle(password)

    return ''.join(password)

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra mayúscula')
    if not re.search(r'[a-z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra minúscula')
    if not re.search(r'\d', password):
        raise ValidationError('La contraseña debe contener al menos un número')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')


class SignUpForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    password1 = PasswordField('Contraseña', validators=[DataRequired(), validate_password_strength])
    password2 = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Registrarse')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('views.home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = form.remember.data
        
        user = Customer.query.filter_by(email=email).first()
        
        if user:
            if check_password_hash(user.password_hash, password):
                # Reiniciar intentos de inicio de sesión
                user.login_attempts = 0
                user.last_attempt = datetime.utcnow()
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                login_user(user, remember=remember)
                flash('Inicio de sesión exitoso', 'success')
                
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                    
                if user.is_first_login:
                    return redirect(url_for('auth.change_password'))
                return redirect(url_for('views.home'))
            else:
                # Incrementar intentos fallidos
                user.login_attempts += 1
                user.last_attempt = datetime.utcnow()
                db.session.commit()
                flash('Contraseña incorrecta', 'error')
        else:
            flash('El email no existe', 'error')
            
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
        
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password1.data
        
        user_exists = Customer.query.filter_by(email=email).first()
        if user_exists:
            flash('El email ya está registrado', 'error')
            return redirect(url_for('auth.sign_up'))
            
        new_user = Customer(
            email=email,
            username=username,
            role='customer'
        )
        new_user.password = password
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cuenta creada exitosamente', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/sign_up.html', form=form)


@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        flash('El usuario no existe.', 'danger')
        return redirect(url_for(HOME_ENDPOINT))
    return render_template('profile.html', customer=customer)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.role != 'super_admin':
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for(HOME_ENDPOINT))
    
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password = form.new_password.data
            current_user.force_password_change = False
            current_user.is_first_login = False
            db.session.commit()
            flash('Contraseña actualizada exitosamente.', 'success')
            return redirect(url_for(HOME_ENDPOINT))
        else:
            flash('Contraseña actual incorrecta.', 'error')
    
    return render_template('auth/change_password.html', form=form)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Customer.query.filter_by(email=email).first()
        
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            msg = Message('Recuperación de Contraseña',
                         sender='noreply@tutienda.com',
                         recipients=[email])
            msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{reset_url}

Si no solicitaste este cambio, ignora este mensaje.
'''
            mail.send(msg)
            flash('Se ha enviado un correo con instrucciones para restablecer tu contraseña.', 'info')
            return redirect(url_for(LOGIN_ENDPOINT))
        
        flash('No se encontró ninguna cuenta con ese correo electrónico.', 'error')
    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('El enlace de recuperación es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = Customer.query.filter_by(email=email).first()
        user.password = form.password.data
        db.session.commit()
        flash('Tu contraseña ha sido actualizada.', 'success')
        return redirect(url_for(LOGIN_ENDPOINT))
    
    return render_template('auth/reset_password.html', form=form)

@auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        security_key = form.security_key.data
        
        # Verificar la clave de seguridad (esto debería estar en una variable de entorno)
        if security_key != os.environ.get('ADMIN_SECURITY_KEY', 'your-security-key'):
            flash('Clave de seguridad incorrecta.', 'error')
            return render_template('auth/edit_profile.html', form=form)
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.address = form.address.data
        
        if form.new_password.data:
            current_user.password = form.new_password.data
        
        db.session.commit()
        flash('Perfil actualizado exitosamente.', 'success')
        return redirect(url_for(HOME_ENDPOINT))
    
    # Pre-llenar el formulario con los datos actuales
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.phone_number.data = current_user.phone_number
    form.address.data = current_user.address
    
    return render_template('auth/edit_profile.html', form=form)

@auth.route('/admin/recovery', methods=['GET', 'POST'])
def admin_recovery():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Customer.query.filter_by(email=email).first()
        
        if user and user.is_admin:
            # Generar un código de recuperación único
            recovery_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Guardar el código en la sesión
            session['recovery_code'] = recovery_code
            session['recovery_email'] = email
            
            # Enviar el código por email (implementar esto según tu sistema de email)
            # send_recovery_email(email, recovery_code)
            
            flash('Se ha enviado un código de recuperación a tu email.', 'info')
            return redirect(url_for('auth.verify_recovery_code'))
        
        flash('No se encontró una cuenta de administrador con ese email.', 'error')
    
    return render_template('auth/admin_recovery.html')

@auth.route('/admin/verify-code', methods=['GET', 'POST'])
def verify_recovery_code():
    if 'recovery_code' not in session or 'recovery_email' not in session:
        flash('Sesión de recuperación expirada.', 'error')
        return redirect(url_for('auth.admin_recovery'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        if code == session['recovery_code']:
            # Código correcto, mostrar formulario para nueva contraseña
            return redirect(url_for('auth.reset_admin_password'))
        
        flash('Código incorrecto.', 'error')
    
    return render_template('auth/verify_recovery_code.html')

@auth.route('/admin/reset-password', methods=['GET', 'POST'])
def reset_admin_password():
    if 'recovery_email' not in session:
        flash('Sesión de recuperación expirada.', 'error')
        return redirect(url_for('auth.admin_recovery'))
    
    if request.method == 'POST':
        email = session['recovery_email']
        user = Customer.query.filter_by(email=email).first()
        
        if user and user.is_admin:
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Las contraseñas no coinciden.', 'error')
                return render_template('auth/reset_admin_password.html')
            
            user.password = new_password
            db.session.commit()
            
            # Limpiar la sesión
            session.pop('recovery_code', None)
            session.pop('recovery_email', None)
            
            flash('Contraseña actualizada exitosamente.', 'success')
            return redirect(url_for(LOGIN_ENDPOINT))
    
    return render_template('auth/reset_admin_password.html')







