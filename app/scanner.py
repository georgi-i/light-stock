"""Barcode/RFID scanner integration routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db, limiter
from app.models import Product
from app.utils import log_audit, record_stock_movement, get_user_language

scanner_bp = Blueprint('scanner', __name__, url_prefix='/scanner')


@scanner_bp.route('/')
@login_required
def index():
    """Scanner main page"""
    return render_template('scanner/index.html')


@scanner_bp.route('/lookup', methods=['GET', 'POST'])
@login_required
def lookup():
    """Quick lookup by barcode/RFID scan"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if not code:
            flash('Please scan or enter a code', 'warning')
            return render_template('scanner/lookup.html')

        # Search by barcode, RFID, or SKU
        product = Product.query.filter(
            (Product.barcode == code) |
            (Product.rfid_tag == code) |
            (Product.sku == code)
        ).first()

        if product:
            log_audit('product_scanned', 'product', product.id, {'code': code})
            return redirect(url_for('inventory.view_product', product_id=product.id))
        else:
            flash(f'No product found with code: {code}', 'danger')

    return render_template('scanner/lookup.html')


@scanner_bp.route('/stock-in', methods=['GET', 'POST'])
@login_required
def stock_in():
    """Add stock by scanning"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        quantity = request.form.get('quantity', 1, type=int)
        notes = request.form.get('notes', '')
        reference = request.form.get('reference', '')

        if not code:
            flash('Please scan or enter a code', 'warning')
            return render_template('scanner/stock_in.html')

        # Find product
        product = Product.query.filter(
            (Product.barcode == code) |
            (Product.rfid_tag == code) |
            (Product.sku == code)
        ).first()

        if not product:
            flash(f'No product found with code: {code}', 'danger')
            return render_template('scanner/stock_in.html')

        try:
            # Record stock movement
            record_stock_movement(
                product=product,
                movement_type='in',
                quantity=quantity,
                notes=notes,
                reference=reference
            )
            db.session.commit()

            log_audit('stock_in_scan', 'product', product.id, {
                'code': code,
                'quantity': quantity
            })

            flash(f'Added {quantity} units to {product.name}. New stock: {product.quantity}', 'success')

            # Clear form for next scan
            return render_template('scanner/stock_in.html', success=True)

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding stock: {str(e)}', 'danger')

    return render_template('scanner/stock_in.html')


@scanner_bp.route('/stock-out', methods=['GET', 'POST'])
@login_required
def stock_out():
    """Remove stock by scanning"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        quantity = request.form.get('quantity', 1, type=int)
        notes = request.form.get('notes', '')
        reference = request.form.get('reference', '')

        if not code:
            flash('Please scan or enter a code', 'warning')
            return render_template('scanner/stock_out.html')

        # Find product
        product = Product.query.filter(
            (Product.barcode == code) |
            (Product.rfid_tag == code) |
            (Product.sku == code)
        ).first()

        if not product:
            flash(f'No product found with code: {code}', 'danger')
            return render_template('scanner/stock_out.html')

        if product.quantity < quantity:
            flash(f'Insufficient stock! Available: {product.quantity}', 'danger')
            return render_template('scanner/stock_out.html')

        try:
            # Record stock movement
            record_stock_movement(
                product=product,
                movement_type='out',
                quantity=quantity,
                notes=notes,
                reference=reference
            )
            db.session.commit()

            log_audit('stock_out_scan', 'product', product.id, {
                'code': code,
                'quantity': quantity
            })

            flash(f'Removed {quantity} units from {product.name}. New stock: {product.quantity}', 'success')

            # Check low stock
            if product.is_low_stock:
                flash(f'Warning: {product.name} is now low on stock!', 'warning')

            # Clear form for next scan
            return render_template('scanner/stock_out.html', success=True)

        except Exception as e:
            db.session.rollback()
            flash(f'Error removing stock: {str(e)}', 'danger')

    return render_template('scanner/stock_out.html')


# API endpoints for quick scanner operations
@scanner_bp.route('/api/scan', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_scan():
    """API endpoint for quick scan operations with rate limiting"""
    data = request.get_json()

    code = data.get('code', '').strip()
    action = data.get('action', 'lookup')  # lookup, stock_in, stock_out
    quantity = data.get('quantity', 1)

    if not code:
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    # Find product
    product = Product.query.filter(
        (Product.barcode == code) |
        (Product.rfid_tag == code) |
        (Product.sku == code)
    ).first()

    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    if action == 'lookup':
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'quantity': product.quantity,
                'min_stock_level': product.min_stock_level,
                'is_low_stock': product.is_low_stock,
                'unit_price': float(product.unit_price)
            }
        })

    elif action == 'stock_in':
        try:
            record_stock_movement(
                product=product,
                movement_type='in',
                quantity=quantity,
                notes='Quick scan stock in'
            )
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Added {quantity} units',
                'new_quantity': product.quantity
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    elif action == 'stock_out':
        if product.quantity < quantity:
            return jsonify({
                'success': False,
                'error': f'Insufficient stock. Available: {product.quantity}'
            }), 400

        try:
            record_stock_movement(
                product=product,
                movement_type='out',
                quantity=quantity,
                notes='Quick scan stock out'
            )
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Removed {quantity} units',
                'new_quantity': product.quantity,
                'is_low_stock': product.is_low_stock
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'Invalid action'}), 400
