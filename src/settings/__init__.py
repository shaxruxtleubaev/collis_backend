"""
Automatically load the correct settings based on DJANGO_SETTINGS_MODULE environment variable

Usage:
- Development: python manage.py runserver (uses local.py by default)
- Production: export DJANGO_SETTINGS_MODULE=src.settings.production
"""

import os

# Default to local settings if not specified
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'src.settings.local')

if 'production' in settings_module:
    from .production import *
else:
    from .local import *