"""
Local development settings
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
# This is just for local development
SECRET_KEY = 'django-insecure-local-dev-key-change-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Database - SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS Settings - Allow localhost for development
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8080',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:3001',
    'http://127.0.0.1:8080',
]

CORS_ALLOW_CREDENTIALS = True

# You can also allow all origins in development (uncomment if needed)
# CORS_ALLOW_ALL_ORIGINS = True

# Update JWT to use this SECRET_KEY
SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY