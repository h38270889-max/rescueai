from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from app.models.user import User, PasswordResetToken
from app.models.audit import AuditLog
from app.forms.auth_forms import (
    RegistrationForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ChangePasswordForm,
    ProfileForm
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip() if form.phone.data else None,
            preferred_language=form.preferred_language.data,
            region=form.region.data.strip() if form.region.data else None,
            consent_emergency_notifications=form.consent_emergency_notifications.data,
            role='user'  # Enforce default role; users can never assign themselves admin
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        AuditLog.log(
            action='USER_REGISTRATION',
            user_id=user.id,
            target_type='user',
            target_id=user.id,
            ip_address=request.remote_addr,
            details=f"New user registered: {user.email}"
        )
        db.session.commit()

        flash('Registration successful! Please sign in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Sign in existing user with password verification."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            user.last_login = datetime.now(timezone.utc)
            session['lang'] = user.preferred_language
            db.session.commit()

            AuditLog.log(
                action='USER_LOGIN',
                user_id=user.id,
                target_type='user',
                target_id=user.id,
                ip_address=request.remote_addr,
                details=f"User logged in: {user.email}"
            )
            db.session.commit()

            flash(f"Welcome back, {user.full_name}!", 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'responder':
                return redirect(url_for('responder.dashboard'))
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please verify your credentials.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out current user and clear session."""
    user_id = current_user.id
    email = current_user.email
    logout_user()
    
    AuditLog.log(
        action='USER_LOGOUT',
        user_id=user_id,
        target_type='user',
        target_id=user_id,
        ip_address=request.remote_addr,
        details=f"User logged out: {email}"
    )
    db.session.commit()
    
    flash('You have been safely signed out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Initiate password reset workflow with single-use expiring token."""
    form = ForgotPasswordForm()
    reset_url = None
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            # Invalidate older unused tokens for this user
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            
            token_str = PasswordResetToken.generate_token_string()
            expires = datetime.now(timezone.utc) + timedelta(hours=1)
            token = PasswordResetToken(user_id=user.id, token=token_str, expires_at=expires)
            db.session.add(token)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=token_str, _external=True)
            flash('Password reset instructions generated. For development/demonstration, your secure reset link is displayed below.', 'info')
        else:
            # Prevent email enumeration by displaying a generic message
            flash('If an account exists with that email address, reset instructions have been generated.', 'info')

    return render_template('auth/forgot_password.html', form=form, reset_url=reset_url)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using a valid token."""
    token_record = PasswordResetToken.query.filter_by(token=token).first()
    if not token_record or not token_record.is_valid():
        flash('This password reset link is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = token_record.user
        user.set_password(form.password.data)
        token_record.used = True
        db.session.commit()

        AuditLog.log(
            action='PASSWORD_RESET_SUCCESS',
            user_id=user.id,
            target_type='user',
            target_id=user.id,
            details=f"Password reset using token for {user.email}"
        )
        db.session.commit()

        flash('Your password has been successfully reset! You can now sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile information."""
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.preferred_language = form.preferred_language.data
        current_user.region = form.region.data.strip() if form.region.data else None
        current_user.consent_emergency_notifications = form.consent_emergency_notifications.data
        session['lang'] = current_user.preferred_language
        db.session.commit()

        flash('Your profile settings have been updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for authenticated user."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()

            AuditLog.log(
                action='PASSWORD_CHANGE',
                user_id=current_user.id,
                target_type='user',
                target_id=current_user.id,
                details=f"Password changed voluntarily by {current_user.email}"
            )
            db.session.commit()

            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect.', 'danger')

    return render_template('auth/change_password.html', form=form)
