# --- timetable/admin.py ---

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Course, Group, Room,
    Lecturer, Student, UserProfile,
    Lesson, Device, Notification
)
from .utils import create_lesson_notification # Import utility
from .signals import _old_lesson_data # Import global dict

# --- Foundation Models ---

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'credits')
    search_fields = ('course_code', 'title')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'intake')
    search_fields = ('name', 'intake')
    list_filter = ('intake',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('building', 'hall', 'capacity')
    search_fields = ('building', 'hall')

# --- User Models ---

class UserProfileInline(admin.StackedInline):
    """Inline view for UserProfile within the standard Django User."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'get_email')
    search_fields = ('fullname',)
    
    def get_email(self, obj):
        # Access the related Django User email via the UserProfile
        return obj.user_profile.user.email
    get_email.short_description = 'Email'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'group', 'get_email')
    search_fields = ('fullname', 'group__name')
    list_filter = ('group',)
    
    def get_email(self, obj):
        return obj.user_profile.user.email
    get_email.short_description = 'Email'

# Customizing the default User Admin to include UserProfile inline
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_user_type')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__user_type')
    
    def get_user_type(self, obj):
        return obj.userprofile.get_user_type_display() if hasattr(obj, 'userprofile') else '-'
    get_user_type.short_description = 'Role'

# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- Scheduling and Notification Models ---

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('date', 'starting_time', 'course', 'lecturer', 'group', 'room')
    list_filter = ('lesson_type', 'date', 'lecturer', 'group')
    search_fields = ('course__title', 'lecturer__fullname', 'room__building', 'room__hall')
    date_hierarchy = 'date'

    # Override save_model to capture old data before it's saved (for the post_save signal)
    def save_model(self, request, obj, form, change):
        if obj.pk: # Only capture if updating existing object
            # Capture the old state before saving
            old_lesson = Lesson.objects.select_related('room', 'lecturer').get(pk=obj.pk)
            _old_lesson_data[obj.pk] = {
                'room_id': old_lesson.room_id,
                'room': old_lesson.room.hall,
                'date': old_lesson.date,
                'starting_time': old_lesson.starting_time,
                'ending_time': old_lesson.ending_time,
                'lecturer_id': old_lesson.lecturer_id,
                'lecturer_fullname': old_lesson.lecturer.fullname,
                'group_id': old_lesson.group_id,
            }
        
        super().save_model(request, obj, form, change)
    
    # Override delete_model to trigger cancellation notification
    def delete_model(self, request, obj):
        # Create cancellation notification BEFORE deleting the lesson instance
        create_lesson_notification(obj, 'CANCELLATION')
        super().delete_model(request, obj)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'platform', 'registration_id', 'created_at')
    list_filter = ('platform',)
    search_fields = ('user_profile__user__username', 'registration_id')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'lesson', 'is_sent', 'created_at')
    list_filter = ('message_type', 'is_sent')
    search_fields = ('message_text', 'lesson__course__title')
    readonly_fields = ('created_at',)