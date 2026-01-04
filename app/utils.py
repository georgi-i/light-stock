"""Utility functions for the IMS application"""
import json
from datetime import datetime
from flask import request, session
from flask_login import current_user
from app import db
from app.models import AuditLog, StockMovement
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64


def log_audit(action, resource_type=None, resource_id=None, details=None):
    """
    Create an audit log entry

    Args:
        action: Action performed (login, logout, create, update, delete)
        resource_type: Type of resource affected (user, product, category)
        resource_id: ID of the resource
        details: Additional details as dict or string
    """
    try:
        # Convert details to JSON if it's a dict
        if isinstance(details, dict):
            details = json.dumps(details)

        audit_entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        # Don't let audit logging break the application
        print(f"Error logging audit: {str(e)}")
        db.session.rollback()


def record_stock_movement(product, movement_type, quantity, notes=None, reference=None):
    """
    Record a stock movement

    Args:
        product: Product instance
        movement_type: 'in', 'out', or 'adjustment'
        quantity: Quantity changed (positive or negative)
        notes: Optional notes
        reference: Optional reference (order number, etc.)

    Returns:
        StockMovement instance
    """
    previous_quantity = product.quantity

    # Calculate new quantity based on movement type
    if movement_type == 'in':
        new_quantity = previous_quantity + abs(quantity)
    elif movement_type == 'out':
        new_quantity = max(0, previous_quantity - abs(quantity))
    elif movement_type == 'adjustment':
        new_quantity = quantity
    else:
        raise ValueError(f"Invalid movement type: {movement_type}")

    # Create stock movement record
    movement = StockMovement(
        product_id=product.id,
        user_id=current_user.id,
        movement_type=movement_type,
        quantity=abs(quantity) if movement_type != 'adjustment' else quantity - previous_quantity,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        notes=notes,
        reference=reference
    )

    # Update product quantity
    product.quantity = new_quantity
    product.updated_at = datetime.utcnow()

    db.session.add(movement)

    return movement


def generate_barcode(code, barcode_type='code128'):
    """
    Generate a barcode image

    Args:
        code: The code to encode
        barcode_type: Type of barcode (code128, ean13, etc.)

    Returns:
        Base64 encoded image string
    """
    try:
        # Get the barcode class
        barcode_class = barcode.get_barcode_class(barcode_type)

        # Generate barcode
        rv = BytesIO()
        barcode_instance = barcode_class(code, writer=ImageWriter())
        barcode_instance.write(rv)

        # Convert to base64
        rv.seek(0)
        barcode_base64 = base64.b64encode(rv.getvalue()).decode('utf-8')

        return f"data:image/png;base64,{barcode_base64}"

    except Exception as e:
        print(f"Error generating barcode: {str(e)}")
        return None


def get_user_language():
    """Get current user's preferred language"""
    if current_user.is_authenticated:
        return current_user.language
    return session.get('language', 'en')


def set_user_language(language):
    """Set user's preferred language"""
    if language not in ['en', 'bg']:
        language = 'en'

    session['language'] = language
    session.modified = True  # Ensure Flask saves the session

    if current_user.is_authenticated:
        current_user.language = language
        db.session.commit()


def format_currency(amount, currency='EUR'):
    """Format amount as currency"""
    if currency == 'EUR':
        return f"€{amount:.2f}"
    return f"${amount:.2f}"


def paginate_query(query, page=1, per_page=20):
    """
    Helper function to paginate a SQLAlchemy query

    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Pagination object
    """
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_low_stock_products():
    """Get all products that are at or below minimum stock level"""
    from app.models import Product
    return Product.query.filter(
        Product.quantity <= Product.min_stock_level
    ).all()


def calculate_inventory_value():
    """Calculate total inventory value"""
    from app.models import Product
    products = Product.query.all()
    return sum(product.total_value for product in products)
