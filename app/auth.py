"""Authentication routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_security import roles_required
from app import db, limiter
from app.models import User, Role
from app.utils import log_audit
from datetime import datetime
import secrets

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login with rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user and user.verify_password(password):
            if not user.active:
                flash('Your account has been deactivated.', 'danger')
                log_audit('login_failed', 'user', user.id, 'Account deactivated')
                return render_template('auth/login.html')

            # Check if 2FA is enabled
            if user.tf_totp_secret:
                session['pending_2fa_user_id'] = user.id
                session['remember_2fa'] = remember
                log_audit('login_2fa_required', 'user', user.id)
                return redirect(url_for('auth.verify_2fa'))

            # Login successful
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            log_audit('login_success', 'user', user.id)
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password', 'danger')
            log_audit('login_failed', details={'username': username_or_email})

    return render_template('auth/login.html')


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def verify_2fa():
    """Verify two-factor authentication code"""
    if 'pending_2fa_user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['pending_2fa_user_id'])
    if not user:
        session.pop('pending_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()

        if user.verify_totp(code):
            # 2FA successful
            remember = session.pop('remember_2fa', False)
            session.pop('pending_2fa_user_id', None)

            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()

            log_audit('login_2fa_success', 'user', user.id)
            flash('Login successful!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid verification code', 'danger')
            log_audit('login_2fa_failed', 'user', user.id)

    return render_template('auth/verify_2fa.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    log_audit('logout', 'user', current_user.id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration disabled - use CLI command"""
    flash('Registration is disabled. Please contact an administrator.', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html')


@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Set up two-factor authentication"""
    if request.method == 'POST':
        if current_user.tf_totp_secret:
            # Disable 2FA
            current_user.tf_totp_secret = None
            current_user.tf_primary_method = None
            db.session.commit()
            log_audit('2fa_disabled', 'user', current_user.id)
            flash('Two-factor authentication has been disabled.', 'info')
        else:
            # Verify and enable 2FA
            code = request.form.get('code', '').strip()
            temp_secret = session.get('temp_totp_secret')

            if temp_secret and current_user.verify_totp(code, temp_secret):
                current_user.tf_totp_secret = temp_secret
                current_user.tf_primary_method = 'authenticator'
                session.pop('temp_totp_secret', None)
                db.session.commit()
                log_audit('2fa_enabled', 'user', current_user.id)
                flash('Two-factor authentication has been enabled!', 'success')
            else:
                flash('Invalid verification code. Please try again.', 'danger')
                return render_template('auth/setup_2fa.html',
                                     qr_code=session.get('temp_qr_code'))

        return redirect(url_for('auth.profile'))

    # Generate new TOTP secret
    import pyotp
    import qrcode
    from io import BytesIO
    import base64

    secret = pyotp.random_base32()
    session['temp_totp_secret'] = secret

    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name='IMS - Inventory Management'
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    qr_code_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    qr_code_data = f"data:image/png;base64,{qr_code_base64}"

    session['temp_qr_code'] = qr_code_data

    return render_template('auth/setup_2fa.html',
                         qr_code=qr_code_data,
                         secret=secret)


# Admin routes
@auth_bp.route('/users')
@login_required
@roles_required('Admin')
def list_users():
    """List all users (Admin only)"""
    users = User.query.all()
    return render_template('auth/users.html', users=users)
