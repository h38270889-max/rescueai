import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if uploaded file has an allowed image extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})

def save_uploaded_image(file_storage):
    """
    Safely validate and store an uploaded image.
    Generates a unique random filename to prevent collisions and path traversal.
    Returns the saved relative filename, or None on failure.
    """
    if not file_storage or not file_storage.filename:
        return None
        
    if not allowed_file(file_storage.filename):
        return None

    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, unique_name)
    file_storage.save(file_path)
    return unique_name

def format_datetime(value, fmt='%b %d, %Y %H:%M'):
    """Format datetime safely for UI rendering."""
    if not value:
        return ""
    return value.strftime(fmt)
