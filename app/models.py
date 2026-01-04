from datetime import datetime
from app import db
from flask_security import UserMixin, RoleMixin
from sqlalchemy import event


# Association table for many-to-many relationship between users and roles
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    """User role model for Flask-Security"""
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model, UserMixin):
    """User model with Flask-Security integration"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)

    # Flask-Security fields
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime())

    # Two-Factor Authentication
    tf_primary_method = db.Column(db.String(64), nullable=True)
    tf_totp_secret = db.Column(db.String(255), nullable=True)

    # User preferences
    language = db.Column(db.String(2), default='en')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    roles = db.relationship('Role', secondary=roles_users,
                          backref=db.backref('users', lazy='dynamic'))
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def is_admin(self):
        return any(role.name == 'Admin' for role in self.roles)

    def set_password(self, password):
        """Hash and set password"""
        from flask_security.utils import hash_password
        self.password = hash_password(password)

    def verify_password(self, password):
        """Verify password"""
        from flask_security.utils import verify_password
        return verify_password(password, self.password)

    def verify_totp(self, code, secret=None):
        """Verify TOTP code"""
        import pyotp
        if secret is None:
            secret = self.tf_totp_secret
        if not secret:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)


class Category(db.Model):
    """Product category model"""
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(100), nullable=False)
    name_bg = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name_en}>'

    def get_name(self, language='en'):
        """Get localized category name"""
        return self.name_bg if language == 'bg' else self.name_en


class Product(db.Model):
    """Product model"""
    id = db.Column(db.Integer, primary_key=True)

    # Product info
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)

    # Product details
    sku = db.Column(db.String(100), unique=True, nullable=False, index=True)
    barcode = db.Column(db.String(100), unique=True, index=True)
    rfid_tag = db.Column(db.String(100), unique=True, index=True)

    # Inventory
    quantity = db.Column(db.Integer, default=0, nullable=False)
    min_stock_level = db.Column(db.Integer, default=10)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)  # Price in EUR

    # Location
    location = db.Column(db.String(100))

    # Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock_movements = db.relationship('StockMovement', backref='product',
                                     lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.sku}>'

    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        return self.quantity <= self.min_stock_level

    @property
    def total_value(self):
        """Calculate total inventory value for this product"""
        return float(self.quantity * self.unit_price)


class StockMovement(db.Model):
    """Track all stock movements (in/out)"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Movement details
    movement_type = db.Column(db.String(20), nullable=False)  # 'in', 'out', 'adjustment'
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)

    # Notes
    notes = db.Column(db.Text)
    reference = db.Column(db.String(100))  # Order number, invoice, etc.

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='stock_movements')

    def __repr__(self):
        return f'<StockMovement {self.movement_type} {self.quantity} of Product {self.product_id}>'


class AuditLog(db.Model):
    """Audit trail for security-sensitive actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Action details
    action = db.Column(db.String(100), nullable=False)  # 'login', 'logout', 'create', 'update', 'delete'
    resource_type = db.Column(db.String(50))  # 'user', 'product', 'category'
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string with additional details

    # Request info
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'


# Event listeners for automatic audit logging
@event.listens_for(Product, 'after_insert')
def log_product_created(mapper, connection, target):
    """Log product creation"""
    # This will be implemented in the audit logging utility
    pass


@event.listens_for(Product, 'after_update')
def log_product_updated(mapper, connection, target):
    """Log product updates"""
    # This will be implemented in the audit logging utility
    pass


@event.listens_for(Product, 'after_delete')
def log_product_deleted(mapper, connection, target):
    """Log product deletion"""
    # This will be implemented in the audit logging utility
    pass
