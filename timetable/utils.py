from .models import Notification
from django.db import transaction
from rest_framework.views import exception_handler

def create_lesson_notification(lesson, message_type, changed_fields=None):
    """
    Utility to create a Notification record based on Lesson changes.
    Stores lesson details so notification persists even if lesson is deleted.
    
    Args:
        lesson: Lesson instance
        message_type: Type of notification (ANNOUNCEMENT, RESCHEDULE, CANCELLATION)
        changed_fields: List of fields that changed (for RESCHEDULE)
    """
    if not changed_fields:
        changed_fields = []

    # Get comma-separated names of all groups assigned to the lesson
    group_names = ", ".join([g.name for g in lesson.groups.all()])
    
    # Build message based on type
    course_code = lesson.course.course_code
    date_str = lesson.date.strftime('%Y-%m-%d')
    time_str = lesson.starting_time.strftime('%H:%M')
    
    base_msg = f"{course_code} for {group_names} on {date_str} at {time_str}"
    
    if message_type == 'CANCELLATION':
        message_text = f"CANCELLED: {base_msg}"
    elif message_type == 'RESCHEDULE':
        # List specific changes
        changes_str = ", ".join(changed_fields)
        message_text = f"UPDATED: {base_msg}. Changes: {changes_str}"
    else:
        # Announcement for new lessons
        message_text = f"NEW LESSON: {base_msg} in {lesson.room.building} - {lesson.room.hall}"

    # Use atomic transaction to ensure the notification is saved reliably
    with transaction.atomic():
        Notification.objects.create(
            lesson=lesson,
            course_code=lesson.course.course_code,
            course_title=lesson.course.title,
            lesson_date=lesson.date,
            lesson_time=lesson.starting_time,
            group_names=group_names,
            message_type=message_type,
            message_text=message_text,
            is_sent=False
        )

def custom_exception_handler(exc, context):
    """
    Custom exception handler that adds status_code to all error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Add status_code to the response
        custom_response_data = {
            'status_code': response.status_code,
            'error': response.data
        }
        
        # If it's a validation error, format it nicely
        if response.status_code == 400:
            custom_response_data['message'] = 'Validation error'
        elif response.status_code == 401:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == 403:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == 500:
            custom_response_data['message'] = 'Internal server error'
        
        response.data = custom_response_data
    
    return response