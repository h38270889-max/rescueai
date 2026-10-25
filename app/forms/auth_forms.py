from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models.user import User

LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('hi', 'हिन्दी (Hindi)'),
    ('mr', 'मराठी (Marathi)'),
    ('bn', 'বাংলা (Bengali)'),
    ('ta', 'தமிழ் (Tamil)'),
    ('te', 'తెలుగు (Telugu)'),
    ('gu', 'ગુજરાતી (Gujarati)'),
    ('kn', 'ಕನ್ನಡ (Kannada)'),
    ('ml', 'മലയാളം (Malayalam)'),
    ('pa', 'ਪੰਜਾਬੀ (Punjabi)'),
    ('ur', 'اردو (Urdu)'),
    ('es', 'Español (Spanish)'),
    ('fr', 'Français (French)'),
    ('ar', 'العربية (Arabic)')
]

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number (Optional)', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    preferred_language = SelectField('Preferred Language', choices=LANGUAGE_CHOICES, default='en')
    region = StringField('City / District / Region', validators=[Optional(), Length(max=100)])
    consent_emergency_notifications = BooleanField(
        'I consent to receive vital emergency alerts and notifications on this platform',
        default=True,
        validators=[DataRequired(message="You must agree to emergency notification terms to register.")]
    )
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with this email address is already registered.')


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Account Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Password Reset Instructions')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Reset Password')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message="Passwords must match.")])
    submit = SubmitField('Update Password')


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    preferred_language = SelectField('Preferred Language', choices=LANGUAGE_CHOICES)
    region = StringField('City / District / Region', validators=[Optional(), Length(max=100)])
    consent_emergency_notifications = BooleanField('Receive emergency broadcast notifications', default=True)
    submit = SubmitField('Save Profile Changes')
