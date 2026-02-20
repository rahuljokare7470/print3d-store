import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration with environment-specific overrides"""

    # Core Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    DEBUG = False
    TESTING = False

    # Database configuration - PostgreSQL on Render, SQLite locally
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'store.db'))
    # Fix Render's postgres:// to postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }

    # Cache configuration - Redis with fallback to simple cache
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', None)
    if CACHE_REDIS_URL:
        CACHE_TYPE = 'redis'
        CACHE_REDIS_URL = CACHE_REDIS_URL
    else:
        CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300

    # Business details
    BUSINESS_NAME = 'PrintCraft 3D'
    BUSINESS_EMAIL = os.environ.get('BUSINESS_EMAIL', 'info@printcraft3d.com')
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '+919876543210')
    BUSINESS_ADDRESS = 'Pune, Maharashtra, India'

    # Admin credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # Payment gateway - Razorpay
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@printcraft3d.com')

    # Order and delivery settings
    FREE_DELIVERY_ABOVE = 999
    DELIVERY_CHARGE = 49
    MIN_ORDER_AMOUNT = 199
    CURRENCY_SYMBOL = '₹'

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

    # Image compression settings
    MAX_IMAGE_SIZE_KB = 150
    MAX_IMAGE_WIDTH = 1200
    IMAGE_QUALITY = 85

    # Compression settings
    COMPRESS_GZIP = True
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

    # Session configuration with security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 24 * 60 * 60  # 24 hours

    # Rate limiting configuration
    RATELIMIT_STORAGE_URL = os.environ.get('CACHE_REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = '200 per day, 50 per hour'

    # Pagination
    ITEMS_PER_PAGE = 12

    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration selector based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Get config based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
