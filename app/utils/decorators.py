from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """Decorator to require that the logged-in user has the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied: Administrator privileges are required to view this page.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def responder_required(f):
    """Decorator to require that the logged-in user is an authorized responder or administrator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_responder:
            flash('Access denied: Authorized responder credentials required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
