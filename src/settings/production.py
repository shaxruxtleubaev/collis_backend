"""
Production settings for PythonAnywhere deployment
"""

from .base import *

# SECURITY WARNING: Generate a unique secret key for production!
# Use this command: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = 'CHANGE-THIS-TO-A-UNIQUE-SECRET-KEY-IN-PRODUCTION'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allow all hosts initially, then change to your specific domain
ALLOWED_HOSTS = ['*']

# For better security, after you know your domain, change to:
# ALLOWED_HOSTS = [
#     'yourusername.pythonanywhere.com',
#     'your-custom-domain.com',
# ]

# Database - SQLite for production (as requested)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'production.sqlite3',
    }
}

# CORS Settings - Allow all origins initially
CORS_ALLOW_ALL_ORIGINS = True

# For better security, after you know your frontend domain, change to:
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = [
#     'https://your-frontend-domain.com',
#     'https://yourusername.pythonanywhere.com',
# ]

CORS_ALLOW_CREDENTIALS = True

# Security Settings for Production
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# Session Security (requires HTTPS)
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
CSRF_COOKIE_SECURE = True     # Only send CSRF cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Note: PythonAnywhere supports HTTPS by default, so these should work fine

# Update JWT to use this SECRET_KEY
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY