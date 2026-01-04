"""Main application routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from app.models import Product, Category, StockMovement
from app.utils import get_low_stock_products, calculate_inventory_value, get_user_language, set_user_language
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page - redirect to dashboard if authenticated"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get statistics
    total_products = Product.query.count()
    low_stock_products = get_low_stock_products()
    total_inventory_value = calculate_inventory_value()

    # Get recent stock movements
    recent_movements = StockMovement.query.order_by(
        StockMovement.created_at.desc()
    ).limit(10).all()

    # Get product categories
    categories = Category.query.all()

    return render_template(
        'dashboard.html',
        total_products=total_products,
        low_stock_count=len(low_stock_products),
        low_stock_products=low_stock_products,
        total_inventory_value=total_inventory_value,
        recent_movements=recent_movements,
        categories=categories
    )


@main_bp.route('/language/<lang>')
def set_language(lang):
    """Change user language preference"""
    if lang in ['en', 'bg']:
        set_user_language(lang)
        # Don't show flash message for language change - it's immediately visible
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/debug/locale')
def debug_locale():
    """Debug route to check locale and session - HTML version"""
    return render_template('debug_locale.html')


@main_bp.route('/debug/babel-config')
def debug_babel_config():
    """Show Babel configuration"""
    from flask import current_app, jsonify
    import os

    trans_dir = current_app.config.get('BABEL_TRANSLATION_DIRECTORIES')
    mo_file = os.path.join(trans_dir, 'bg', 'LC_MESSAGES', 'messages.mo') if trans_dir else 'N/A'

    return jsonify({
        'BABEL_TRANSLATION_DIRECTORIES': trans_dir,
        'translation_dir_exists': os.path.exists(trans_dir) if trans_dir else False,
        'mo_file_path': mo_file,
        'mo_file_exists': os.path.exists(mo_file) if trans_dir else False,
        'app_root': current_app.root_path,
        'BABEL_DEFAULT_LOCALE': current_app.config.get('BABEL_DEFAULT_LOCALE')
    })
