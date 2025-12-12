# --- timetable/signals.py ---

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lesson
from .utils import create_lesson_notification

# Dictionary to temporarily store the old lesson data before save/update.
# This data is set in the LessonAdmin or LessonViewSet (if we re-added the logic there).
_old_lesson_data = {}

@receiver(post_save, sender=Lesson)
def lesson_save_notification(sender, instance, created, **kwargs):
    """
    Handles notification trigger after a Lesson is created or updated.
    """
    global _old_lesson_data
    
    if created:
        # Lesson Creation
        create_lesson_notification(instance, 'ANNOUNCEMENT', changed_fields=['New Lesson'])
        
    else:
        # Lesson Update
        old_lesson = _old_lesson_data.pop(instance.pk, None)
        
        if old_lesson:
            changed_fields = []
            message_type = 'RESCHEDULE'
            
            # Room change
            if old_lesson['room_id'] != instance.room_id:
                changed_fields.append(f"Room changed from {old_lesson['room']} to {instance.room.hall}")
                message_type = 'ROOM_CHANGE'
                
            # Date/Time change
            if old_lesson['date'] != instance.date or \
               old_lesson['starting_time'] != instance.starting_time or \
               old_lesson['ending_time'] != instance.ending_time:
                changed_fields.append("Date/Time changed")
                
            # Lecturer change
            if old_lesson['lecturer_id'] != instance.lecturer_id:
                 changed_fields.append(f"Lecturer changed from {old_lesson['lecturer_fullname']} to {instance.lecturer.fullname}")

            if changed_fields:
                create_lesson_notification(instance, message_type, changed_fields)