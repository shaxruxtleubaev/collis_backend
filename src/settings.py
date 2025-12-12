"""
Django settings for collis_backend project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-some-secret-key' # Replace this in production

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'jazzmin', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Your apps
    'timetable.apps.TimetableConfig', # <--- CHANGE HERE
    'rest_framework',
    'drf_spectacular'
    
    # ... any other apps ...
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3', # This will create a file named db.sqlite3 in the project root
    }
}

# ... (other standard settings like AUTH_PASSWORD_VALIDATORS, LANGUAGE_CODE, etc.)

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    # Site Configuration
    "site_title": "ColliS Timetable Admin",
    "site_header": "ColliS",
    "site_brand": "Scheduling System",
    "welcome_sign": "Welcome to the ColliS Scheduling Administration Panel",
    "copyright": "Timetable Management System",

    # UI Customization
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "theme": "flatly", 
    "show_ui_builder": False, # Set to True initially to customize, then False for production
    
    # Specific format for TimeField input in admin
    "time_format_field": "%H:%M", # Ensures time is shown/input as HH:MM
    
    # Menu Configuration (to keep admin clean)
    "order_with_respect_to": [
        "auth",
        "timetable",
        "timetable.group",
        "timetable.course",
        "timetable.room",
        "timetable.lecturer",
        "timetable.student",
        "timetable.lesson",
        "timetable.notification",
    ],
}

# ----------------------------------------
# 3. REST FRAMEWORK & AUTHENTICATION
# ----------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Use Simple JWT for all token-based API access
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        
        # Include session authentication for use with the DRF browsable API and Admin
        'rest_framework.authentication.SessionAuthentication', 
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        # Ensure only authenticated users can access the API by default
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# ----------------------------------------
# 4. SIMPLE JWT SETTINGS
# ----------------------------------------

from datetime import timedelta

SIMPLE_JWT = {
    # Set the token expiration times
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # Access token lasts 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # Refresh token lasts 1 month
    
    # Allow users to submit credentials for new token pair
    'ROTATE_REFRESH_TOKENS': True, 
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, # Uses your existing Django SECRET_KEY
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}


# ----------------------------------------
# 5. DRF SPECTACULAR (SWAGGER) SETTINGS
# ----------------------------------------

SPECTACULAR_SETTINGS = {
    'TITLE': 'ColliS Timetable Management API',
    'DESCRIPTION': 'API documentation for the ColliS Scheduling System, including lesson management, conflict detection, and user profiles.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False, # Serve UI separate from schema endpoint
    # You can add JWT to the list of security schemes
    'SECURITY': [
        {
            "Bearer Auth": [],
        }
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'defaultModelRendering': 'example',
        'tryItOutEnabled': True,
    }
}