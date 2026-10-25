from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app.forms.incident_forms import INCIDENT_CATEGORY_CHOICES

AUDIENCE_CHOICES = [
    ('all', 'All Consented Users (Global Broadcast)'),
    ('region', 'Targeted Regional Broadcast (City / District)'),
    ('category', 'Targeted by Emergency Category')
]

URGENCY_CHOICES = [
    ('Critical', 'Critical — Immediate Life Safety Threat'),
    ('High', 'High — Urgent Precautionary Warning'),
    ('Medium', 'Medium — General Advisory / Weather Warning')
]

class CreateAlertForm(FlaskForm):
    title = StringField('Alert Headline', validators=[DataRequired(), Length(min=5, max=150)])
    category = SelectField('Disaster / Incident Category', choices=INCIDENT_CATEGORY_CHOICES, validators=[DataRequired()])
    urgency = SelectField('Urgency Level', choices=URGENCY_CHOICES, default='High', validators=[DataRequired()])
    target_audience = SelectField('Target Audience', choices=AUDIENCE_CHOICES, default='all', validators=[DataRequired()])
    target_region = StringField('Target Region (Required if Regional Broadcast)', validators=[Optional(), Length(max=100)])
    message = TextAreaField('Public Alert Message & Protective Instructions', validators=[DataRequired(), Length(min=10, max=2500)])
    submit = SubmitField('Dispatch Emergency Alert')
