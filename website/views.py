from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Product, Cart, Order, Category
from flask_login import login_required, current_user
from . import db
from intasend import APIService
from .forms import ShopItemsForm
from werkzeug.utils import secure_filename
import os


views = Blueprint('views', __name__)

API_PUBLISHABLE_KEY = 'YOUR_PUBLISHABLE_KEY'

API_TOKEN = 'YOUR_API_TOKEN'


@views.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True).all()
    categories = Category.query.all()
    return render_template('home.html', 
                         items=items, 
                         categories=categories,
                         cart=Cart.query.filter_by(customer_link=current_user.id).all() if current_user.is_authenticated else [])


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f' Quantity of { item_exists.product.product_name } has been updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not Updated', e)
            flash(f'Quantity of { item_exists.product.product_name } not updated')
            return redirect(request.referrer)

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} added to cart')
    except Exception as e:
        print('Item not added to cart', e)
        flash(f'{new_cart_item.product.product_name} has not been added to cart')

    return redirect(request.referrer)


@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount+200)


@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

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
        cart_item.quantity = cart_item.quantity - 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id)
    if customer_cart:
        try:
            total = 0
            for item in customer_cart:
                total += item.product.current_price * item.quantity

            service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
            create_order_response = service.collect.mpesa_stk_push(phone_number='YOUR_NUMBER ', email=current_user.email,
                                                                   amount=total + 200, narrative='Purchase of goods')

            for item in customer_cart:
                new_order = Order()
                new_order.quantity = item.quantity
                new_order.price = item.product.current_price
                new_order.status = create_order_response['invoice']['state'].capitalize()
                new_order.payment_id = create_order_response['id']

                new_order.product_link = item.product_link
                new_order.customer_link = item.customer_link

                db.session.add(new_order)

                product = Product.query.get(item.product_link)

                product.in_stock -= item.quantity

                db.session.delete(item)

                db.session.commit()

            flash('Order Placed Successfully')

            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed')
            return redirect('/')
    else:
        flash('Your cart is Empty')
        return redirect('/')


@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)


@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')


@views.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ShopItemsForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product_name = form.product_name.data
        current_price = form.current_price.data
        previous_price = form.previous_price.data
        discount_percentage = form.discount_percentage.data
        in_stock = form.in_stock.data
        flash_sale = form.flash_sale.data
        category_id = form.category_id.data
        
        file = form.product_picture.data
        file_name = secure_filename(file.filename)
        file_path = f'./media/{file_name}'
        file.save(file_path)

        new_product = Product()
        new_product.product_name = product_name
        new_product.current_price = current_price
        new_product.previous_price = previous_price
        new_product.in_stock = in_stock
        new_product.flash_sale = flash_sale
        new_product.product_picture = file_path

        try:
            db.session.add(new_product)
            db.session.commit()
            flash('Producto agregado exitosamente')
            return redirect('/')
        except Exception as e:
            flash('Error al agregar el producto')
            print(e)
            
    return render_template('add_product.html', form=form)


@views.route('/list-products')
def list_products():
    items = Product.query.all()
    return render_template('list_products.html', items=items)


@views.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        new_category = Category(name=name, description=description)
        try:
            db.session.add(new_category)
            db.session.commit()
            flash('Categoría agregada exitosamente')
        except Exception as e:
            flash('Error al agregar la categoría')
            print(e)
            
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@views.route('/delete-category/<int:category_id>')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Categoría eliminada exitosamente')
    except Exception as e:
        flash('Error al eliminar la categoría')
        print(e)
    return redirect('/categories')


@views.route('/edit-category/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    if current_user.id != 1:
        flash('No tienes permiso para editar categorías')
        return redirect('/')
        
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        try:
            category.name = name
            category.description = description
            db.session.commit()
            flash('Categoría actualizada exitosamente')
            return redirect('/categories')
        except Exception as e:
            flash('Error al actualizar la categoría')
            print(e)
            
    return render_template('edit_category.html', category=category)


def delete_product_image(image_path):
    if image_path and image_path.startswith('/static/'):
        # Convert URL path to filesystem path
        full_path = os.path.join(os.path.dirname(__file__), image_path.lstrip('/'))
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                return True
            except Exception as e:
                print(f"Error deleting image: {e}")
    return False

@views.route('/delete-product/<int:product_id>')
@login_required
def delete_product(product_id):
    if current_user.id != 1:
        flash('No tienes permiso para eliminar productos')
        return redirect('/')
        
    product = Product.query.get_or_404(product_id)
    
    # Delete the product image first
    if product.product_picture:
        delete_product_image(product.product_picture)
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Producto eliminado exitosamente')
    except Exception as e:
        flash('Error al eliminar el producto')
        print(e)
    
    return redirect('/')

@views.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.id != 1:
        flash('No tienes permiso para editar productos')
        return redirect('/')
        
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        if 'product_picture' in request.files:
            file = request.files['product_picture']
            if file.filename != '':
                # Delete old image first
                if product.product_picture:
                    delete_product_image(product.product_picture)
                
                # Save new image
                file_name = secure_filename(file.filename)
                file_path = f'/static/media/{file_name}'
                full_path = os.path.join(os.path.dirname(__file__), f'.{file_path}')
                file.save(full_path)
                product.product_picture = file_path
        
        # Update other fields
        product.product_name = request.form.get('product_name')
        product.current_price = float(request.form.get('current_price'))
        product.previous_price = float(request.form.get('previous_price'))
        product.in_stock = int(request.form.get('in_stock'))
        product.category_id = int(request.form.get('category_id'))
        product.flash_sale = 'flash_sale' in request.form
        
        try:
            db.session.commit()
            flash('Producto actualizado exitosamente')
            return redirect('/')
        except Exception as e:
            flash('Error al actualizar el producto')
            print(e)
            
    return render_template('edit_product.html', product=product, categories=categories)














