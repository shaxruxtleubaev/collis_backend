from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender='timetable.Lesson')
def capture_old_lesson_data(sender, instance, **kwargs):
    """Capture the old lesson data before it's updated"""
    if instance.pk:  # Only for updates, not new lessons
        try:
            from .models import Lesson
            old_obj = Lesson.objects.get(pk=instance.pk)
            instance._old_data = {
                'course_id': old_obj.course_id,
                'course_code': old_obj.course.course_code,
                'lecturer_id': old_obj.lecturer_id,
                'lecturer_name': old_obj.lecturer.fullname,
                'room_id': old_obj.room_id,
                'room_name': f"{old_obj.room.building} - {old_obj.room.hall}",
                'lesson_type': old_obj.lesson_type,
                'date': old_obj.date,
                'starting_time': old_obj.starting_time,
                'ending_time': old_obj.ending_time,
                'group_ids': set(old_obj.groups.values_list('id', flat=True))
            }
        except sender.DoesNotExist:
            instance._old_data = None
    else:
        instance._old_data = None

@receiver(post_save, sender='timetable.Lesson')
def lesson_save_notification(sender, instance, created, **kwargs):
    """Create notification when lesson is created or updated"""
    from .utils import create_lesson_notification
    
    if created:
        # New lesson created
        create_lesson_notification(instance, 'ANNOUNCEMENT')
    else:
        # Lesson updated - check what changed
        if hasattr(instance, '_old_data') and instance._old_data:
            old_data = instance._old_data
            changed_fields = []
            
            # Check each field for changes
            if old_data['course_id'] != instance.course_id:
                changed_fields.append(f"Course changed to {instance.course.course_code}")
            
            if old_data['lecturer_id'] != instance.lecturer_id:
                changed_fields.append(f"Lecturer changed to {instance.lecturer.fullname}")
            
            if old_data['room_id'] != instance.room_id:
                changed_fields.append(f"Room changed to {instance.room.building} - {instance.room.hall}")
            
            if old_data['lesson_type'] != instance.lesson_type:
                changed_fields.append(f"Type changed to {instance.get_lesson_type_display()}")
            
            if old_data['date'] != instance.date:
                changed_fields.append(f"Date changed to {instance.date}")
            
            if old_data['starting_time'] != instance.starting_time:
                changed_fields.append(f"Start time changed to {instance.starting_time.strftime('%H:%M')}")
            
            if old_data['ending_time'] != instance.ending_time:
                changed_fields.append(f"End time changed to {instance.ending_time.strftime('%H:%M')}")
            
            # Get current group IDs
            current_group_ids = set(instance.groups.values_list('id', flat=True))
            if old_data['group_ids'] != current_group_ids:
                changed_fields.append("Groups changed")
            
            # Create notification if anything changed
            if changed_fields:
                create_lesson_notification(instance, 'RESCHEDULE', changed_fields)
            
            # Clean up the temporary data
            delattr(instance, '_old_data')