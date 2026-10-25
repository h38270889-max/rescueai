import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'resqai-dev-secret-key-super-safe-982341')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f"sqlite:///{BASE_DIR / 'instance' / 'resqai.db'}"
    )
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB Max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # CSRF & Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600 * 24  # 24 hours
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # AI Services (OpenAI & Gemini)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # Duplicate Detection Parameters
    DUPLICATE_SIMILARITY_THRESHOLD = 0.55
    DUPLICATE_DISTANCE_KM_THRESHOLD = 5.0
    DUPLICATE_TIME_WINDOW_HOURS = 24
    
    # Multilingual
    DEFAULT_LANGUAGE = 'en'
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English', 'dir': 'ltr'},
        'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'dir': 'ltr'},
        'mr': {'name': 'Marathi', 'native': 'मराठी', 'dir': 'ltr'},
        'bn': {'name': 'Bengali', 'native': 'বাংলা', 'dir': 'ltr'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'dir': 'ltr'},
        'te': {'name': 'Telugu', 'native': 'తెలుగు', 'dir': 'ltr'},
        'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'dir': 'ltr'},
        'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'dir': 'ltr'},
        'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'dir': 'ltr'},
        'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'dir': 'ltr'},
        'ur': {'name': 'Urdu', 'native': 'اردو', 'dir': 'rtl'},
        'es': {'name': 'Spanish', 'native': 'Español', 'dir': 'ltr'},
        'fr': {'name': 'French', 'native': 'Français', 'dir': 'ltr'},
        'ar': {'name': 'Arabic', 'native': 'العربية', 'dir': 'rtl'}
    }
    
    # Emergency Categories
    EMERGENCY_CATEGORIES = [
        'medical',
        'fire',
        'flood',
        'earthquake',
        'road_accident',
        'missing_person',
        'trapped_person',
        'rescue_request',
        'shelter_request',
        'other'
    ]
    
    # India Emergency Directory Defaults
    EMERGENCY_DIRECTORY = {
        'pan_india': '112',
        'police': '100',
        'fire': '101',
        'ambulance': '102 / 108',
        'disaster_management_ndrf': '1078',
        'women_helpline': '1091',
        'child_helpline': '1098'
    }

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-12345'

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
