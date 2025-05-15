from flask import Blueprint, render_template, flash, redirect, request, jsonify, url_for
from .models import Product, Cart, Order, Category, Customer, OrderItem
from flask_login import login_required, current_user
from . import db
# from intasend import APIService
from .forms import ShopItemsForm, EditProfileForm
from werkzeug.utils import secure_filename
import os
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from datetime import datetime
import logging

views = Blueprint('views', __name__)
logging.basicConfig(level=logging.ERROR)
API_PUBLISHABLE_KEY = 'YOUR_PUBLISHABLE_KEY'
MESSAGES_NO_PERMIT = 'No tienes permisos para realizar esta acción.'
API_TOKEN = 'YOUR_API_TOKEN'


@views.route('/')
def home():
    show_profile_modal = False
    form = None
    if current_user.is_authenticated and getattr(current_user, 'is_first_login', False):
        form = EditProfileForm()
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.phone_number.data = current_user.phone_number
        form.address.data = current_user.address
        show_profile_modal = True
    try:
        items = Product.query.filter(Product.stock_quantity > 0).all()
        categories = Category.query.all()
        cart = Cart.query.filter_by(customer_id=current_user.id).all() if current_user.is_authenticated else []
    except Exception as e:
        print(f"Error loading data: {e}")
        items = []
        categories = []
        cart = []
    return render_template('home.html', items=items, categories=categories, cart=cart, show_profile_modal=show_profile_modal, form=form)


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    if current_user.role in ['admin', 'super_admin']:
        flash('Los administradores no pueden agregar productos al carrito', 'error')
        return redirect(url_for('views.home'))
        
    product = Product.query.get_or_404(item_id)
    if product.stock_quantity <= 0:
        flash('Producto sin stock', 'error')
        return redirect(url_for('views.home'))
        
    cart = Cart.query.filter_by(customer_id=current_user.id).first()
    if not cart:
        cart = Cart(customer_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
        
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
        
    db.session.commit()
    flash('Producto agregado al carrito', 'success')
    return redirect(url_for('views.cart'))


@views.route('/cart')
@login_required
def cart():
    if current_user.role in ['admin', 'super_admin']:
        flash('Los administradores no pueden acceder al carrito', 'error')
        return redirect(url_for('views.home'))
        
    cart = Cart.query.filter_by(customer_id=current_user.id).first()
    if not cart:
        cart = Cart(customer_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
        
    items = CartItem.query.filter_by(cart_id=cart.id).all()
    total = sum(item.product.current_price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=total)


@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        cart_item.total_price = cart_item.quantity * cart_item.product.current_price
        db.session.commit()

        cart = Cart.query.filter_by(customer_id=current_user.id).all()

        amount = 0
        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)

@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        if cart_item.quantity > 1:
            cart_item.quantity = cart_item.quantity - 1
            cart_item.total_price = cart_item.quantity * cart_item.product.current_price
            db.session.commit()

        cart = Cart.query.filter_by(customer_id=current_user.id).all()

        amount = 0
        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)

@views.route('/removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_id=current_user.id).all()

        amount = 0
        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('/place-order')
@login_required
def place_order():
    # Verificar si el usuario es administrador
    if current_user.is_admin:
        flash('Los administradores no pueden realizar pedidos.', 'warning')
        return redirect(url_for('views.home'))
        
    customer_cart = Cart.query.filter_by(customer_id=current_user.id).all()
    if not customer_cart:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('views.home'))
    
    try:
        # Verificar stock y calcular total
        total = 0
        for item in customer_cart:
            product = Product.query.get(item.product_id)
            if not product:
                flash(f'El producto {item.product.product_name} ya no está disponible', 'error')
                return redirect(url_for('views.show_cart'))
            
            if product.stock_quantity < item.quantity:
                flash(f'No hay suficiente stock de {product.product_name}. Stock disponible: {product.stock_quantity}', 'error')
                return redirect(url_for('views.show_cart'))
            
            total += product.current_price * item.quantity

        # Crear la orden
        new_order = Order(
            customer_id=current_user.id,
            status='pending',
            total=total,
            shipping_address=current_user.address
        )
        db.session.add(new_order)
        
        # Crear items de la orden y actualizar stock
        for item in customer_cart:
            product = Product.query.get(item.product_id)
            
            # Crear item de la orden
            order_item = OrderItem(
                order=new_order,
                product_id=product.id,
                quantity=item.quantity,
                price=product.current_price
            )
            db.session.add(order_item)
            
            # Actualizar stock
            product.stock_quantity -= item.quantity
            product.in_stock = product.stock_quantity > 0
            
            # Eliminar item del carrito
            db.session.delete(item)
        
        db.session.commit()
        flash('Pedido realizado exitosamente', 'success')
        return redirect(url_for('views.order'))
        
    except Exception as e:
        db.session.rollback()
        print('Error al procesar el pedido:', e)
        flash('Error al procesar el pedido. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('views.show_cart'))


@views.route('/orders')
@login_required
def orders():
    if current_user.role in ['admin', 'super_admin']:
        flash('Los administradores no pueden acceder a los pedidos', 'error')
        return redirect(url_for('views.home'))
        
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.date.desc()).all()
    return render_template('orders.html', orders=orders)


@views.route('/api/search/suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip().lower()
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    # Obtener productos que coincidan con la consulta (con límite razonable)
    products = Product.query.filter(
        (Product.product_name.ilike(f'%{query}%')) |
        (Product.description.ilike(f'%{query}%'))
    ).limit(10).all()
    
    # Obtener categorías que coincidan con la consulta
    categories = Category.query.filter(
        Category.name.ilike(f'%{query}%')
    ).limit(5).all()
    
    # Diccionario para mantener seguimiento de sugerencias y su relevancia
    suggestions = {}
    
    # Función para calcular la puntuación de relevancia
    def calculate_relevance(term, source_term, is_category=False):
        term = term.lower()
        source_term = source_term.lower()
        
        # Puntuación base basada en la posición de coincidencia
        position = term.find(source_term)
        if position == 0:
            score = 1.0  # Coincidencia al inicio
        else:
            score = 0.5  # Coincidencia en otra parte
            
        # Bonus por ser categoría
        if is_category:
            score += 0.2
            
        # Bonus por longitud (preferir términos más largos)
        score += min(0.3, len(term) * 0.02)
        
        return score
    
    # Procesar productos
    for product in products:
        # Añadir el nombre completo del producto
        if query in product.product_name.lower():
            score = calculate_relevance(product.product_name, query)
            suggestions[product.product_name] = max(score, suggestions.get(product.product_name, 0))
        
        # Añadir palabras clave del nombre del producto
        for word in product.product_name.split():
            word_lower = word.lower()
            if len(word) > 2 and query in word_lower and word_lower != query:
                score = calculate_relevance(word, query)
                suggestions[word] = max(score, suggestions.get(word, 0))
    
    # Procesar categorías
    for category in categories:
        if query in category.name.lower():
            score = calculate_relevance(category.name, query, is_category=True)
            suggestions[category.name] = max(score, suggestions.get(category.name, 0))
    
    # Ordenar sugerencias por puntuación (más relevantes primero)
    sorted_suggestions = sorted(
        suggestions.items(),
        key=lambda x: (-x[1], len(x[0]))  # Primero por puntuación, luego por longitud
    )
    
    # Tomar las 8 mejores sugerencias únicas
    unique_suggestions = []
    seen_terms = set()
    
    for term, _ in sorted_suggestions:
        term_lower = term.lower()
        if term_lower not in seen_terms and term_lower != query:
            unique_suggestions.append(term)
            seen_terms.add(term_lower)
            if len(unique_suggestions) >= 8:
                break
    
    # Si hay pocas sugerencias, intentar con búsqueda difusa
    if len(unique_suggestions) < 5 and len(query) > 2:
        from difflib import get_close_matches
        
        # Obtener todos los términos de productos y categorías para búsqueda difusa
        all_terms = set()
        for product in Product.query.with_entities(Product.product_name).limit(1000).all():
            all_terms.update(word.lower() for word in product[0].split() if len(word) > 2)
        
        # Buscar términos similares
        fuzzy_matches = get_close_matches(query, all_terms, n=5, cutoff=0.6)
        
        # Añadir sugerencias difusas únicas
        for match in fuzzy_matches:
            if match not in seen_terms:
                unique_suggestions.append(match)
                seen_terms.add(match)
                if len(unique_suggestions) >= 8:
                    break
    
    return jsonify({'suggestions': unique_suggestions})

@views.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(
            Product.product_name.ilike(f'%{query}%') |
            Product.description.ilike(f'%{query}%')
        ).all()
    else:
        products = []
    return render_template('search.html', products=products, query=query)

@views.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash(MESSAGES_NO_PERMIT, 'error')
        return redirect(url_for('views.home'))
    
    form = ShopItemsForm()
    
    if form.validate_on_submit():
        try:
            # Manejar la subida de la imagen
            product_picture = '/static/images/default-product.jpg'  # Imagen por defecto
            if form.product_picture.data:
                file = form.product_picture.data
                if file and file.filename:
                    # Verificar la extensión del archivo
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('Formato de archivo no permitido. Use: png, jpg, jpeg, gif', 'error')
                        return redirect(url_for('views.add_product'))
                    
                    # Crear directorio de uploads si no existe
                    upload_folder = os.path.join('website', 'static', 'uploads', 'products')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generar nombre único para el archivo
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Guardar la ruta relativa para la base de datos
                    product_picture = os.path.join('static', 'uploads', 'products', filename).replace('\\', '/')
            
            # Crear el nuevo producto
            new_product = Product(
                product_name=form.product_name.data,
                description=form.description.data,
                current_price=form.current_price.data,
                previous_price=form.previous_price.data if form.previous_price.data else None,
                in_stock=form.in_stock.data,
                stock_quantity=form.stock_quantity.data,
                flash_sale=form.flash_sale.data,
                product_picture=product_picture,
                category_id=form.category_id.data,
                created_by=current_user.id
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash('Producto agregado exitosamente!', 'success')
            return redirect(url_for('views.list_products'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar producto: {str(e)}")
            flash('Ocurrió un error al agregar el producto', 'error')
    
    # Si es GET o hay un error, mostrar el formulario
    return render_template('product/add_product.html', form=form)


@views.route('/list-products')
def list_products():
    # Obtener todos los productos y categorías
    products = Product.query.all()
    categories = Category.query.all()
    
    # Obtener parámetros de filtrado de la URL
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'name_asc')
    
    # Aplicar filtros
    query = Product.query
    
    # Filtrar por categoría si se especifica
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Filtrar por búsqueda
    if search_query:
        query = query.filter(Product.product_name.ilike(f'%{search_query}%'))
    
    # Aplicar ordenamiento
    if sort == 'name_asc':
        query = query.order_by(Product.product_name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Product.product_name.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.current_price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.current_price.desc())
    else:
        query = query.order_by(Product.id.desc())
    
    # Obtener los productos filtrados
    items = query.all()
    
    return render_template('product/list_products.html', 
                         items=items,  # Cambiado de products a items
                         categories=categories,
                         selected_category=category_id,
                         search_query=search_query,
                         sort=sort)
@views.route('/delete-item/<int:item_id>')
@login_required
def delete_item(item_id):
    if not current_user.is_admin:
        flash(MESSAGES_NO_PERMIT, 'error')
        return redirect(url_for('views.home'))
        
    try:
        item_to_delete = Product.query.get_or_404(item_id)
        if not item_to_delete:
            flash('El producto no existe', 'error')
            return redirect(url_for('views.list_products'))
            
        nombre = item_to_delete.product_name
        db.session.delete(item_to_delete)
        db.session.commit()
        flash(f'El producto "{nombre}" ha sido eliminado exitosamente', 'success')
    except Exception as e:
        print('Error al eliminar:', e)
        db.session.rollback()
        flash('Error al eliminar el producto', 'error')
    return redirect(url_for('views.list_products'))


@views.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    if not current_user.is_admin:
        flash('No tienes permiso para editar productos', 'error')
        return redirect(url_for('views.list_products'))
        
    product = Product.query.get_or_404(item_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            product.product_name = request.form.get('product_name', product.product_name)
            
            # Handle numeric fields with validation
            try:
                current_price = request.form.get('current_price')
                previous_price = request.form.get('previous_price')
                stock_quantity = request.form.get('in_stock')  # Este campo viene del formulario como 'in_stock'
                
                if current_price is not None and current_price != '':
                    product.current_price = float(current_price)
                if previous_price is not None and previous_price != '':
                    product.previous_price = float(previous_price)
                if stock_quantity is not None and stock_quantity != '':
                    stock_quantity = int(stock_quantity)
                    product.stock_quantity = stock_quantity
                    # Actualizar el estado in_stock basado en la cantidad
                    product.in_stock = stock_quantity > 0
            except (ValueError, TypeError) as e:
                flash('Error en los valores numéricos. Asegúrese de ingresar números válidos.', 'error')
                return redirect(url_for('views.edit_item', item_id=item_id))
                
            product.flash_sale = 'flash_sale' in request.form
            
            # Manejar la subida de la imagen
            imagen_actualizada = False
            if 'product_picture' in request.files:
                file = request.files['product_picture']
                if file and file.filename:
                    # Verificar la extensión del archivo
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(file.filename)
                        # Agregar timestamp al nombre del archivo para evitar duplicados
                        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                        # Asegurarse de que el directorio existe
                        upload_dir = os.path.join('website', 'static', 'uploads', 'products')
                        os.makedirs(upload_dir, exist_ok=True)
                        # Guardar el archivo
                        file_path = os.path.join(upload_dir, filename)
                        file.save(file_path)
                        # Actualizar la ruta de la imagen en el producto
                        product.product_picture = f'/static/uploads/products/{filename}'
                        imagen_actualizada = True
                    else:
                        flash('Tipo de archivo no permitido. Use PNG, JPG, JPEG o GIF.', 'error')
                        return redirect(url_for('views.edit_item', item_id=item_id))
            # Si no se subió imagen y el campo está vacío o null, poner la imagen por defecto
            if not imagen_actualizada and (not product.product_picture or product.product_picture.strip() == '' or product.product_picture is None):
                product.product_picture = '/static/images/default-product.jpg'
            
            db.session.commit()
            flash(f'Producto "{product.product_name}" actualizado exitosamente', 'success')
            return redirect(url_for('views.list_products'))
        except Exception as e:
            db.session.rollback()
            print('Error al actualizar:', e)
            flash(f'Error al actualizar el producto: {str(e)}', 'error')
            return redirect(url_for('views.edit_item', item_id=item_id))
    
    return render_template('product/edit_product.html', product=product)


@views.route('/confirm-delete/<int:item_id>')
def confirm_delete(item_id):
    product = Product.query.get_or_404(item_id)
    return render_template('product/confirm_delete.html', product=product)


@views.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    icon = StringField('Icon')

@views.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if not (current_user.is_admin or current_user.is_super_admin):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('views.home'))
    form = CategoryForm()
    if form.validate_on_submit():
        try:
            new_category = Category(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(new_category)
            db.session.commit()
            flash('Category created successfully', 'success')
            return redirect(url_for('views.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
    return render_template('categoria/agregar_categoria.html', form=form)

@views.route('/category/<int:category_id>/edit')
@login_required
def edit_category(category_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('views.home'))
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    return render_template('categoria/editar_categoria.html', category=category, form=form)

@views.route('/category/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category_post(category_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    category = Category.query.get_or_404(category_id)
    form = CategoryForm()
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.icon = form.icon.data
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('views.categories'))
    
    return render_template('categoria/editar_categoria.html', category=category, form=form)

@views.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully', 'success')
    return redirect(url_for('views.categories'))

@views.route('/category/<int:category_id>/products')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    query = request.args.get('q', '')
    
    if query:
        products = Product.query.filter(
            Product.category_id == category_id,
            (Product.product_name.ilike(f'%{query}%')) |
            (Product.description.ilike(f'%{query}%'))
        ).all()
    else:
        products = Product.query.filter_by(category_id=category_id).all()
        
    return render_template('category_products.html', category=category, products=products, query=query)

@views.route('/make_admin/<int:user_id>')
@login_required
def make_admin(user_id):
    # Solo el primer usuario puede hacer esto, o alguien que ya es admin
    if current_user.id != 1 and not current_user.is_admin:
        flash('You do not have permission to do this.', 'error')
        return redirect(url_for('views.home'))
    
    user = Customer.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash(f'User {user.username} is now an admin', 'success')
    return redirect(url_for('views.home'))

@views.route('/create-sample-categories')
@login_required
def create_sample_categories():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('views.home'))
    
    sample_categories = [
        {
            'name': 'Electronics',
            'description': 'Electronic devices and accessories',
            'icon': 'fa fa-laptop'
        },
        {
            'name': 'Clothing',
            'description': 'Fashion and apparel',
            'icon': 'fa fa-tshirt'
        },
        {
            'name': 'Books',
            'description': 'Books and literature',
            'icon': 'fa fa-book'
        },
        {
            'name': 'Home & Kitchen',
            'description': 'Home appliances and kitchen items',
            'icon': 'fa fa-home'
        },
        {
            'name': 'Sports',
            'description': 'Sports equipment and accessories',
            'icon': 'fa fa-futbol'
        }
    ]
    
    try:
        for category_data in sample_categories:
            # Check if category already exists
            existing_category = Category.query.filter_by(name=category_data['name']).first()
            if not existing_category:
                new_category = Category(
                    name=category_data['name'],
                    description=category_data['description'],
                    icon=category_data['icon']
                )
                db.session.add(new_category)
        
        db.session.commit()
        flash('Sample categories created successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating sample categories: {str(e)}', 'error')
    
    return redirect(url_for('views.categories'))

@views.route('/evaluation/module-quality')
@login_required
def module_quality():
    if not current_user.is_admin:
        flash('Acceso no autorizado. Solo los administradores pueden ver esta página.', 'error')
        return redirect(url_for('views.home'))
    return render_template('evaluation/module_quality.html')

@views.route('/evaluation/usage-quality')
@login_required
def usage_quality():
    if not current_user.is_admin:
        flash('Acceso no autorizado. Solo los administradores pueden ver esta página.', 'error')
        return redirect(url_for('views.home'))
    return render_template('evaluation/usage_quality.html')

@views.route('/profile')
@login_required
def profile():
    if current_user.role in ['admin', 'super_admin']:
        flash('Los administradores no pueden acceder al perfil de cliente', 'error')
        return redirect(url_for('views.home'))
    return render_template('cliente/profile.html')

@views.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if current_user.role in ['admin', 'super_admin']:
        flash('Los administradores no pueden actualizar el perfil de cliente', 'error')
        return redirect(url_for('views.home'))
        
    try:
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
    # En el bloque except
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error al actualizar el perfil: {e}')
        flash('Error al actualizar el perfil', 'error')
        
    return redirect(url_for('views.profile'))

@views.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    if request.method == 'POST':
        preferences = {
            'email_notifications': request.form.get('email_notifications') == 'on',
            'sms_notifications': request.form.get('sms_notifications') == 'on',
            'show_profile': request.form.get('show_profile') == 'on'
        }
        current_user.preferences = preferences
        db.session.commit()
        flash('Preferencias actualizadas exitosamente.', 'success')
        return redirect(url_for('views.profile'))

@views.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('No tienes permisos para acceder a esta página.', 'error')
        return redirect(url_for('views.home'))
    return render_template('admin/dashboard.html')

@views.route('/admin/add_user', methods=['POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        flash(MESSAGES_NO_PERMIT, 'error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if Customer.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'error')
            return redirect(url_for('views.admin'))

        new_user = Customer(
            username=username,
            email=email,
            role=role
        )
        new_user.password = password
        db.session.add(new_user)
        db.session.commit()
        flash('Usuario agregado exitosamente.', 'success')
        return redirect(url_for('views.admin'))

@views.route('/admin/add_product', methods=['POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash(MESSAGES_NO_PERMIT, 'error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category_id = int(request.form.get('category'))

        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id
        )

        # Handle product image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join('website/static/uploads/products', filename))
                new_product.image = f'/static/uploads/products/{filename}'

        db.session.add(new_product)
        db.session.commit()
        flash('Producto agregado exitosamente.', 'success')
        return redirect(url_for('views.admin'))

@views.route('/admin/update_settings', methods=['POST'])
@login_required
def update_settings():
    if not current_user.is_admin:
        flash(MESSAGES_NO_PERMIT, 'error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        # Update application settings
        maintenance_mode = request.form.get('maintenance_mode') == 'on'
        email_notifications = request.form.get('email_notifications') == 'on'
        
        # Here you would typically update these settings in a configuration file or database
        flash('Configuración actualizada exitosamente.', 'success')
        return redirect(url_for('views.admin'))

@views.route('/login')
def login_redirect():
    return redirect(url_for('auth.login'))

@views.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product/detail.html', product=product)

@views.route('/about')
def about():
    return render_template('about.html')

@views.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':        
        # Aquí podrías agregar la lógica para enviar el email
        flash('Mensaje enviado exitosamente', 'success')
        return redirect(url_for('views.contact'))
        
    return render_template('contact.html')














