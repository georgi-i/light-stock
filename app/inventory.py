"""Inventory management routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Category, StockMovement
from app.utils import (log_audit, record_stock_movement, generate_barcode,
                      get_user_language, paginate_query)

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@inventory_bp.route('/products')
@login_required
def list_products():
    """List all products with search and filter"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    low_stock = request.args.get('low_stock', False, type=bool)

    query = Product.query

    # Search filter
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (Product.barcode.ilike(f'%{search}%'))
        )

    # Category filter
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Low stock filter
    if low_stock:
        query = query.filter(Product.quantity <= Product.min_stock_level)

    # Order by name
    query = query.order_by(Product.name)

    # Paginate
    pagination = paginate_query(query, page=page, per_page=20)

    categories = Category.query.all()

    return render_template(
        'inventory/products.html',
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        selected_category=category_id,
        low_stock=low_stock
    )


@inventory_bp.route('/product/<int:product_id>')
@login_required
def view_product(product_id):
    """View product details"""
    product = Product.query.get_or_404(product_id)

    # Get stock movement history
    movements = StockMovement.query.filter_by(
        product_id=product_id
    ).order_by(StockMovement.created_at.desc()).limit(50).all()

    return render_template(
        'inventory/product_detail.html',
        product=product,
        movements=movements
    )


@inventory_bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        sku = request.form.get('sku')
        barcode_value = request.form.get('barcode', '')
        quantity = request.form.get('quantity', 0, type=int)
        min_stock_level = request.form.get('min_stock_level', 10, type=int)
        unit_price = request.form.get('unit_price', 0, type=float)
        location = request.form.get('location', '')
        category_id = request.form.get('category_id', type=int)

        # Validation
        if not name or not sku:
            flash('Name and SKU are required', 'danger')
            return render_template('inventory/product_form.html',
                                 categories=Category.query.all())

        # Check for duplicate SKU
        if Product.query.filter_by(sku=sku).first():
            flash('SKU already exists', 'danger')
            return render_template('inventory/product_form.html',
                                 categories=Category.query.all())

        # Create product
        product = Product(
            name=name,
            description=description,
            sku=sku,
            barcode=barcode_value if barcode_value else None,
            quantity=quantity,
            min_stock_level=min_stock_level,
            unit_price=unit_price,
            location=location,
            category_id=category_id if category_id else None
        )

        db.session.add(product)
        db.session.commit()

        # Log initial stock if quantity > 0
        if quantity > 0:
            record_stock_movement(
                product=product,
                movement_type='in',
                quantity=quantity,
                notes='Initial stock'
            )
            db.session.commit()

        log_audit('product_created', 'product', product.id, {
            'sku': sku,
            'name': name
        })

        flash(f'Product {sku} added successfully!', 'success')
        return redirect(url_for('inventory.view_product', product_id=product.id))

    categories = Category.query.all()
    return render_template('inventory/product_form.html', categories=categories)


@inventory_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # Update product fields
        product.name = request.form.get('name')
        product.description = request.form.get('description', '')
        product.sku = request.form.get('sku')
        product.barcode = request.form.get('barcode', '')
        product.min_stock_level = request.form.get('min_stock_level', 10, type=int)
        product.unit_price = request.form.get('unit_price', 0, type=float)
        product.location = request.form.get('location', '')

        category_id = request.form.get('category_id', type=int)
        product.category_id = category_id if category_id else None

        db.session.commit()

        log_audit('product_updated', 'product', product.id, {
            'sku': product.sku,
            'name': product.name
        })

        flash(f'Product {product.sku} updated successfully!', 'success')
        return redirect(url_for('inventory.view_product', product_id=product.id))

    categories = Category.query.all()
    return render_template('inventory/product_form.html',
                         product=product,
                         categories=categories)


@inventory_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)

    sku = product.sku
    log_audit('product_deleted', 'product', product.id, {'sku': sku})

    db.session.delete(product)
    db.session.commit()

    flash(f'Product {sku} deleted successfully!', 'success')
    return redirect(url_for('inventory.list_products'))


@inventory_bp.route('/product/<int:product_id>/stock', methods=['POST'])
@login_required
def adjust_stock(product_id):
    """Adjust product stock"""
    product = Product.query.get_or_404(product_id)

    movement_type = request.form.get('movement_type')  # 'in', 'out', 'adjustment'
    quantity = request.form.get('quantity', 0, type=int)
    notes = request.form.get('notes', '')
    reference = request.form.get('reference', '')

    if movement_type not in ['in', 'out', 'adjustment']:
        flash('Invalid movement type', 'danger')
        return redirect(url_for('inventory.view_product', product_id=product_id))

    if quantity <= 0 and movement_type != 'adjustment':
        flash('Quantity must be greater than 0', 'danger')
        return redirect(url_for('inventory.view_product', product_id=product_id))

    try:
        record_stock_movement(
            product=product,
            movement_type=movement_type,
            quantity=quantity,
            notes=notes,
            reference=reference
        )
        db.session.commit()

        log_audit('stock_adjusted', 'product', product.id, {
            'sku': product.sku,
            'movement_type': movement_type,
            'quantity': quantity
        })

        flash(f'Stock adjusted for {product.sku}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adjusting stock: {str(e)}', 'danger')

    return redirect(url_for('inventory.view_product', product_id=product_id))


@inventory_bp.route('/product/<int:product_id>/barcode')
@login_required
def product_barcode(product_id):
    """Generate and display barcode for product"""
    product = Product.query.get_or_404(product_id)

    if not product.barcode:
        flash('Product does not have a barcode', 'warning')
        return redirect(url_for('inventory.view_product', product_id=product_id))

    barcode_image = generate_barcode(product.barcode)

    return render_template('inventory/barcode.html',
                         product=product,
                         barcode_image=barcode_image)


# Category routes
@inventory_bp.route('/categories')
@login_required
def list_categories():
    """List all categories"""
    categories = Category.query.all()
    return render_template('inventory/categories.html', categories=categories)


@inventory_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Add new category"""
    if request.method == 'POST':
        name_en = request.form.get('name_en')
        name_bg = request.form.get('name_bg')
        description = request.form.get('description', '')

        if not name_en or not name_bg:
            flash('Category name in both languages is required', 'danger')
            return render_template('inventory/category_form.html')

        category = Category(
            name_en=name_en,
            name_bg=name_bg,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        log_audit('category_created', 'category', category.id, {
            'name_en': name_en
        })

        flash(f'Category {name_en} added successfully!', 'success')
        return redirect(url_for('inventory.list_categories'))

    return render_template('inventory/category_form.html')


# API endpoints for AJAX
@inventory_bp.route('/api/search')
@login_required
def api_search():
    """Search products API endpoint"""
    query = request.args.get('q', '')

    if len(query) < 2:
        return jsonify([])

    products = Product.query.filter(
        (Product.name.ilike(f'%{query}%')) |
        (Product.sku.ilike(f'%{query}%')) |
        (Product.barcode.ilike(f'%{query}%'))
    ).limit(10).all()

    results = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode,
            'quantity': p.quantity
        }
        for p in products
    ]

    return jsonify(results)
