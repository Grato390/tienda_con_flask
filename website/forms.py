from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, length, NumberRange, Email, EqualTo, ValidationError, Length
from flask_wtf.file import FileField, FileRequired
import re

MESSAGE_CONTRA_MENOR_8 = 'La contraseña debe tener al menos 8 caracteres'
NOM_USER = 'Nombre de Usuario'
CONFIRM_CONTRA = 'Confirmar Contraseña'
PASSWO = 'Contraseña'
MESSAGE_CONTR_COINCIDIR = 'Las contraseñas deben coincidir'
def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError(MESSAGE_CONTRA_MENOR_8)
    if not re.search(r'[A-Z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra mayúscula')
    if not re.search(r'[a-z]', password):
        raise ValidationError('La contraseña debe contener al menos una letra minúscula')
    if not re.search(r'\d', password):
        raise ValidationError('La contraseña debe contener al menos un número')


class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    username = StringField(NOM_USER, validators=[DataRequired(), length(min=2)])
    password1 = PasswordField(PASSWO, validators=[DataRequired(), validate_password_strength])
    password2 = PasswordField(CONFIRM_CONTRA, validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Registrarse')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField(PASSWO, validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')


class ShopItemsForm(FlaskForm):
    # Información básica
    product_name = StringField('Nombre del Producto', validators=[
        DataRequired(message='El nombre del producto es requerido'),
        Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
    ])
    
    description = StringField('Descripción', validators=[
        Length(max=500, message='La descripción no puede exceder los 500 caracteres')
    ])
    
    # Precios
    current_price = FloatField('Precio Actual', validators=[
        DataRequired(message='El precio actual es requerido'),
        NumberRange(min=0.01, message='El precio debe ser mayor a 0')
    ])
    
    previous_price = FloatField('Precio Anterior (opcional)', validators=[
        NumberRange(min=0, message='El precio no puede ser negativo')
    ])
    
    # Stock y disponibilidad
    in_stock = BooleanField('¿En stock?', default=True)
    stock_quantity = IntegerField('Cantidad en Stock', validators=[
        DataRequired(message='La cantidad es requerida'),
        NumberRange(min=0, message='La cantidad no puede ser negativa')
    ], default=0)
    
    # Categoría
    category_id = SelectField('Categoría', coerce=int, validators=[
        DataRequired(message='Seleccione una categoría')
    ])
    
    # Imagen del producto
    product_picture = FileField('Imagen del Producto', validators=[
        FileRequired(message='La imagen del producto es requerida')
    ])
    
    # Ofertas
    flash_sale = BooleanField('¿En oferta flash?')
    
    # Botones de acción
    add_product = SubmitField('Guardar Producto')
    update_product = SubmitField('Actualizar Producto')
    
    def __init__(self, *args, **kwargs):
        super(ShopItemsForm, self).__init__(*args, **kwargs)
        # Cargar las categorías disponibles
        from .models import Category
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]


class OrderForm(FlaskForm):
    order_status = SelectField('Order Status', choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'),
                                                        ('Out for delivery', 'Out for delivery'),
                                                        ('Delivered', 'Delivered'), ('Canceled', 'Canceled')])

    update = SubmitField('Update Status')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(),
        Length(min=8, message=MESSAGE_CONTRA_MENOR_8),
        validate_password_strength
    ])
    confirm_password = PasswordField(CONFIRM_CONTRA, validators=[
        DataRequired(),
        EqualTo('password', message=MESSAGE_CONTR_COINCIDIR)
    ])
    submit = SubmitField('Restablecer Contraseña')


class EditProfileForm(FlaskForm):
    username = StringField(NOM_USER, validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Número de Teléfono')
    address = StringField('Dirección')
    security_key = PasswordField('Clave de Seguridad', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña (opcional)', validators=[
        Length(min=8, message=MESSAGE_CONTRA_MENOR_8),
        validate_password_strength
    ])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[
        EqualTo('new_password', message=MESSAGE_CONTR_COINCIDIR)
    ])
    submit = SubmitField('Actualizar Perfil')


class CreateAdminForm(FlaskForm):
    username = StringField(NOM_USER, validators=[
        DataRequired(),
        Length(min=2, max=150, message='El nombre de usuario debe tener entre 2 y 150 caracteres')
    ])
    email = EmailField('Correo Electrónico', validators=[
        DataRequired(),
        Email(message='Por favor, ingrese un correo electrónico válido')
    ])
    password = PasswordField(PASSWO, validators=[
        DataRequired(),
        validate_password_strength,
        Length(min=8, message=MESSAGE_CONTRA_MENOR_8)
    ])
    confirm_password = PasswordField(CONFIRM_CONTRA, validators=[
        DataRequired(),
        EqualTo('password', message=MESSAGE_CONTR_COINCIDIR)
    ])
    role = SelectField('Rol', choices=[
        ('admin', 'Administrador'),
        ('super_admin', 'Super Administrador')
    ], validators=[DataRequired()])
    security_question1 = StringField('Pregunta de Seguridad 1', validators=[
        DataRequired(),
        Length(min=10, message='La pregunta de seguridad debe tener al menos 10 caracteres')
    ])
    security_answer1 = StringField('Respuesta de Seguridad 1', validators=[
        DataRequired(),
        Length(min=3, message='La respuesta debe tener al menos 3 caracteres')
    ])
    security_question2 = StringField('Pregunta de Seguridad 2', validators=[
        DataRequired(),
        Length(min=10, message='La pregunta de seguridad debe tener al menos 10 caracteres')
    ])
    security_answer2 = StringField('Respuesta de Seguridad 2', validators=[
        DataRequired(),
        Length(min=3, message='La respuesta debe tener al menos 3 caracteres')
    ])
    force_password_change = BooleanField('Forzar cambio de contraseña en primer inicio de sesión', default=True)
    submit = SubmitField('Crear Administrador')





