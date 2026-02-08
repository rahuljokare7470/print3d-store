"""
Configuration file for the 3D Print Store application.

HOW TO MODIFY:
- Change SECRET_KEY to any random string (keep it secret in production!)
- Update MAIL_* settings with your actual email credentials
- Change ADMIN_USERNAME and ADMIN_PASSWORD before deploying
- Set WHATSAPP_NUMBER to your business WhatsApp number (with country code, no +)
"""

import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ─── Security ───────────────────────────────────────────────
    # IMPORTANT: Change this to a random string in production!
    # You can generate one in Python: import secrets; secrets.token_hex(32)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-key-in-production')

    # ─── Database ───────────────────────────────────────────────
    # SQLite database file stored in the project folder
    # No external database server needed!
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'store.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Saves memory

    # ─── File Uploads ───────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

    # ─── Image Optimization ────────────────────────────────────
    MAX_IMAGE_WIDTH = 1200   # Resize large images to this width
    THUMBNAIL_SIZE = (400, 400)  # Product card thumbnails

    # ─── Admin Credentials ──────────────────────────────────────
    # CHANGE THESE before deploying your site!
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'print3d@2026')

    # ─── Email Settings ─────────────────────────────────────────
    # For Gmail: Enable "App Passwords" in your Google Account security
    # Then generate an app password and use it here
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')  # your-email@gmail.com
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')  # app password from Google
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', '')

    # ─── Business Details ───────────────────────────────────────
    BUSINESS_NAME = 'PrintCraft 3D'
    BUSINESS_TAGLINE = 'Premium 3D Printed Products'
    BUSINESS_EMAIL = os.environ.get('BUSINESS_EMAIL', 'rahuljokare7470@gmail.com')
    BUSINESS_PHONE = os.environ.get('BUSINESS_PHONE', '+91 9890304065')
    BUSINESS_ADDRESS = 'Solapur, Maharashtra, India'

    # WhatsApp number WITHOUT the + sign (e.g., 919876543210)
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '919890304065')

    # Google Maps embed coordinates for Pune
    GOOGLE_MAPS_LAT = '17.659920'
    GOOGLE_MAPS_LNG = '75.906387'

    # ─── Pricing ────────────────────────────────────────────────
    CURRENCY_SYMBOL = '₹'
    MIN_ORDER_AMOUNT = 199  # Minimum order in INR
    FREE_DELIVERY_ABOVE = 999  # Free delivery above this amount
    DELIVERY_CHARGE = 49  # Delivery charge in INR
