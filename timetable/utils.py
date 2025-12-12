# --- timetable/utils.py ---

from .models import Notification, Lecturer, Student, Lesson
from django.db import transaction

def create_lesson_notification(lesson, message_type, changed_fields=None):
    """
    Creates a Notification record when a lesson is changed (created, updated, or deleted).
    In a complete system, this would also trigger the push notification service (e.g., Firebase).
    """
    if not changed_fields:
        changed_fields = []

    # 1. Construct the message text
    
    # Base message for all types
    base_msg = f"Lesson {lesson.course.course_code} ({lesson.course.title}) on {lesson.date.strftime('%Y-%m-%d')} has been "
    
    if message_type == 'CANCELLATION':
        message_text = base_msg + "CANCELLED."
    elif message_type == 'RESCHEDULE':
        # Detail changes like date/time
        if changed_fields:
            change_list = ", ".join(changed_fields)
            message_text = base_msg + f"RESCHEDULED. Changes: {change_list}. New time: {lesson.starting_time.strftime('%H:%M')} - {lesson.ending_time.strftime('%H:%M')}."
        else:
             message_text = base_msg + f"RESCHEDULED. New time: {lesson.starting_time.strftime('%H:%M')} - {lesson.ending_time.strftime('%H:%M')}."
    elif message_type == 'ROOM_CHANGE':
         message_text = base_msg + f"moved. New room: {lesson.room.building} - {lesson.room.hall}."
    elif message_type == 'ANNOUNCEMENT':
         message_text = base_msg + "SCHEDULED."
    else: # Default for other updates
        message_text = base_msg + "UPDATED."

    # 2. Save the notification record
    with transaction.atomic():
        Notification.objects.create(
            lesson=lesson,
            message_type=message_type,
            message_text=message_text,
            is_sent=False # Set to True after successful push notification dispatch
        )
        
    # NOTE: Actual push dispatch logic would go here.