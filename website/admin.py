import json
from datetime import datetime
from flask import Blueprint, render_template, flash, send_from_directory, redirect, request, url_for
from flask_login import login_required, current_user
from .forms import ShopItemsForm, OrderForm, CreateAdminForm
from werkzeug.utils import secure_filename
from .models import Product, Order, Customer
from . import db
from werkzeug.security import generate_password_hash

admin = Blueprint('admin', __name__)

PERMISSION_DENIED_MESSAGE = 'No tienes permiso para acceder a esta página'
HOME_ENDPOINT = 'views.home'
ACTION_DENIED_MESSAGE = 'No tienes permiso para realizar esta acción'
ADMIN_MANAGEMENT_ENDPOINT = 'admin.admin_management'
SHOP_ITEMS_ENDPOINT = 'admin.shop_items'

# Constantes para plantillas
NOT_FOUND_TEMPLATE = '404.html'

@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    # Solo administradores pueden agregar productos
    if not current_user.is_admin:
        flash(PERMISSION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    form = ShopItemsForm()
    if request.method == 'POST' and form.validate_on_submit():
        product_name = form.product_name.data
        current_price = form.current_price.data
        previous_price = form.previous_price.data
        in_stock = form.in_stock.data
        flash_sale = form.flash_sale.data

        file = form.product_picture.data
        file_name = secure_filename(file.filename)
        file_path = f'./media/{file_name}'

        try:
            file.save(file_path)

            new_shop_item = Product(
                product_name=product_name,
                current_price=current_price,
                previous_price=previous_price,
                in_stock=in_stock,
                flash_sale=flash_sale,
                product_picture=file_path,
                created_by=current_user.id
            )

            db.session.add(new_shop_item)
            db.session.commit()
            flash(f'Producto "{product_name}" agregado exitosamente', 'success')
            return redirect(url_for(SHOP_ITEMS_ENDPOINT))

        except Exception as e:
            db.session.rollback()
            print(f'Error al agregar producto: {str(e)}')
            flash('Error al agregar el producto', 'danger')

    return render_template('add_shop_items.html', form=form)

@admin.route('/shop-items')
@login_required
def shop_items():
    # Solo administradores pueden ver la lista de productos
    if not current_user.is_admin:
        flash(PERMISSION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    items = Product.query.order_by(Product.date_added.desc()).all()
    return render_template('shop_items.html', items=items)

@admin.route('/admin-management')
@login_required
def admin_management():
    # Solo super administradores pueden acceder a la gestión de administradores
    if not current_user.is_super_admin:
        flash(PERMISSION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    # Obtener solo administradores (no clientes normales)
    users = Customer.query.filter(
        Customer.role.in_(['super_admin', 'admin'])
    ).order_by(
        db.case(
            (Customer.role == 'super_admin', 1),
            (Customer.role == 'admin', 2),
            else_=3
        ),
        Customer.username
    ).all()

    return render_template('admin/admin_management.html', users=users)

@admin.route('/update-user-role/<int:user_id>', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.is_super_admin:
        flash(ACTION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    user = Customer.query.get_or_404(user_id)
    new_role = request.form.get('new_role')

    # Validar que el rol sea válido
    if new_role not in ['user', 'admin', 'super_admin']:
        flash('Rol no válido', 'danger')
        return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

    # No permitir modificar el rol del super admin principal
    if user.role == 'super_admin' and user.email == 'admin@tienda.com':
        flash('No puedes modificar el rol del super administrador principal', 'danger')
        return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

    # No permitir que un usuario se quite sus propios permisos de administrador
    if user.id == current_user.id and new_role == 'user':
        flash('No puedes quitarte a ti mismo los permisos de administrador', 'danger')
        return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

    try:
        user.role = new_role
        db.session.commit()
        flash(f'Rol de {user.username} actualizado exitosamente a {new_role.replace("_", " ").title()}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el rol del usuario', 'danger')
        print(f'Error al actualizar rol: {str(e)}')

    return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

@admin.route('/create-admin', methods=['GET', 'POST'])
@login_required
def create_admin():
    # Solo super administradores pueden crear nuevos administradores
    if not current_user.is_super_admin:
        flash(ACTION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    form = CreateAdminForm()

    if form.validate_on_submit():
        # Verificar si el email ya existe
        existing_user = Customer.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Ya existe un usuario con este correo electrónico', 'danger')
            return redirect(url_for('admin.create_admin'))

        # Verificar si el nombre de usuario ya existe
        existing_username = Customer.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Este nombre de usuario ya está en uso', 'danger')
            return redirect(url_for('admin.create_admin'))

        # Crear el nuevo administrador
        new_admin = Customer(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),  # Almacenar la contraseña como hash
            role=form.role.data,  # Usar el rol seleccionado en el formulario
            is_first_login=True,
            force_password_change=form.force_password_change.data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Configurar preguntas de seguridad
        security_questions = {
            'question1': form.security_question1.data,
            'answer1': form.security_answer1.data,
            'question2': form.security_question2.data,
            'answer2': form.security_answer2.data
        }
        new_admin.security_questions = json.dumps(security_questions)

        try:
            db.session.add(new_admin)
            db.session.commit()
            flash('Administrador creado exitosamente', 'success')
            return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el administrador', 'danger')
            print(f'Error al crear administrador: {str(e)}')

    return render_template('admin/create_admin.html', form=form)

@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    # Solo administradores pueden actualizar productos
    if not current_user.is_admin:
        flash(PERMISSION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    item_to_update = Product.query.get_or_404(item_id)
    form = ShopItemsForm(obj=item_to_update)

    if form.validate_on_submit():
        try:
            # Actualizar campos del producto
            item_to_update.product_name = form.product_name.data
            item_to_update.current_price = form.current_price.data
            item_to_update.previous_price = form.previous_price.data
            item_to_update.in_stock = form.in_stock.data
            item_to_update.flash_sale = form.flash_sale.data

            # Manejar la carga de la nueva imagen si se proporciona
            if form.product_picture.data:
                file = form.product_picture.data
                file_name = secure_filename(file.filename)
                file_path = f'./media/{file_name}'
                file.save(file_path)
                item_to_update.product_picture = file_path

            item_to_update.updated_at = datetime.utcnow()

            db.session.commit()
            flash(f'Producto "{item_to_update.product_name}" actualizado exitosamente', 'success')
            return redirect(url_for(SHOP_ITEMS_ENDPOINT))

        except Exception as e:
            db.session.rollback()
            print(f'Error al actualizar producto: {str(e)}')
            flash('Error al actualizar el producto', 'danger')

    return render_template('update_item.html', form=form, item=item_to_update)

@admin.route('/delete-item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    # Solo administradores pueden eliminar productos
    if not current_user.is_admin:
        flash(ACTION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    try:
        item_to_delete = Product.query.get_or_404(item_id)
        product_name = item_to_delete.product_name
        db.session.delete(item_to_delete)
        db.session.commit()
        flash(f'Producto "{product_name}" eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        print(f'Error al eliminar producto: {str(e)}')
        flash('Error al eliminar el producto', 'danger')

    return redirect(url_for(SHOP_ITEMS_ENDPOINT))

@admin.route('/delete-admin/<int:admin_id>', methods=['POST'])
@login_required
def delete_admin(admin_id):
    if not current_user.is_super_admin:
        flash(ACTION_DENIED_MESSAGE, 'danger')
        return redirect(url_for(HOME_ENDPOINT))

    # No permitir auto-eliminación
    if current_user.id == admin_id:
        flash('No puedes eliminarte a ti mismo', 'danger')
        return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

    admin_to_delete = Customer.query.get_or_404(admin_id)

    # No permitir eliminar al super admin principal
    if admin_to_delete.role == 'super_admin' and admin_to_delete.email == 'admin@tienda.com':
        flash('No puedes eliminar al super administrador principal', 'danger')
        return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

    try:
        db.session.delete(admin_to_delete)
        db.session.commit()
        flash('Administrador eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el administrador', 'danger')
        print(e)

    return redirect(url_for(ADMIN_MANAGEMENT_ENDPOINT))

@admin.route('/view-orders')
@login_required
def order_view():
    if current_user.id == 1:
        orders = Order.query.all()
        return render_template('view_orders.html', orders=orders)
    return render_template(NOT_FOUND_TEMPLATE)

@admin.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order(order_id):
    if current_user.id == 1:
        form = OrderForm()

        order = Order.query.get(order_id)

        if form.validate_on_submit():
            status = form.order_status.data
            order.status = status

            try:
                db.session.commit()
                flash(f'Order {order_id} Updated successfully')
                return redirect('/view-orders')
            except Exception as e:
                print(e)
                flash(f'Order {order_id} not updated')
                return redirect('/view-orders')

        return render_template('order_update.html', form=form)

    return render_template(NOT_FOUND_TEMPLATE)

@admin.route('/customers')
@login_required
def display_customers():
    if current_user.id == 1:
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)
    return render_template(NOT_FOUND_TEMPLATE)

@admin.route('/admin-page')
@login_required
def admin_page():
    if current_user.id == 1:
        return render_template('admin.html')
    return render_template(NOT_FOUND_TEMPLATE)