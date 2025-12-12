# --- timetable/apps.py ---

from django.apps import AppConfig

class TimetableConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timetable'

    def ready(self):
        # Import signal handlers when Django starts
        import timetable.signals