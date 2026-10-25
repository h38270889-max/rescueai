from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.forms.auth_forms import LANGUAGE_CHOICES

INCIDENT_CATEGORY_CHOICES = [
    ('medical', 'Medical Emergency (Heart attack, injury, breathing, etc.)'),
    ('fire', 'Fire & Explosion (Building fire, smoke, cylinder blast)'),
    ('flood', 'Flood & Rising Waters (Submerged, current, stranded)'),
    ('earthquake', 'Earthquake & Tremor (Building collapse, trapped)'),
    ('road_accident', 'Road & Traffic Accident (Collision, vehicle rollover)'),
    ('missing_person', 'Missing Person (Separated child, elderly missing)'),
    ('trapped_person', 'Trapped Person (Stuck in elevator, collapsed room)'),
    ('rescue_request', 'Urgent Rescue / Evacuation Request (SOS, boat needed)'),
    ('shelter_request', 'Shelter & Relief Camp Request (Homeless, food, water)'),
    ('other', 'Other Emergency')
]

INCIDENT_STATUS_CHOICES = [
    ('Submitted', 'Submitted (New)'),
    ('Under Review', 'Under Review (Triage)'),
    ('Assigned', 'Assigned (Responder Dispatched)'),
    ('In Progress', 'In Progress (Active Operation)'),
    ('Resolved', 'Resolved (Victims Secured)'),
    ('Closed', 'Closed')
]

class EmergencyReportForm(FlaskForm):
    category = SelectField('Incident Category', choices=INCIDENT_CATEGORY_CHOICES, validators=[DataRequired()])
    description = TextAreaField('Description of the Emergency (Write in your preferred language)', validators=[DataRequired(), Length(min=10, max=3000)])
    original_language = SelectField('Message Language', choices=LANGUAGE_CHOICES, default='en')
    contact_name = StringField('Your Name or On-Scene Contact', validators=[Optional(), Length(max=100)])
    contact_phone = StringField('Callback Phone Number', validators=[Optional(), Length(max=30)])
    location_address = StringField('Location / Landmark / Street Address', validators=[Optional(), Length(max=255)])
    latitude = FloatField('Latitude (Optional)', validators=[Optional()])
    longitude = FloatField('Longitude (Optional)', validators=[Optional()])
    affected_count = IntegerField('Estimated Number of People Affected', default=1, validators=[DataRequired(), NumberRange(min=1, max=10000)])
    image = FileField('Upload Scene Photo (Optional, PNG/JPG/WEBP max 5MB)', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Only images (PNG, JPG, WEBP) are allowed!')])
    consent = BooleanField('I confirm this information is genuine and understand ResQAI assists responders but does not replace official emergency services (112)', default=True, validators=[DataRequired()])
    submit = SubmitField('Submit Emergency Report')


class IncidentUpdateForm(FlaskForm):
    status = SelectField('Incident Status', choices=INCIDENT_STATUS_CHOICES, validators=[DataRequired()])
    assigned_responder_id = SelectField('Assign Responder', coerce=int, validators=[Optional()])
    responder_notes = TextAreaField('Responder Operations Log & Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Update Incident Record')
