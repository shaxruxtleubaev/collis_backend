from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Course, Group, Room,
    Lecturer, Student, UserProfile,
    Lesson, Notification
)
from .utils import create_lesson_notification 

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'credits', 'created_at')
    search_fields = ('course_code', 'title')
    ordering = ('course_code',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'intake', 'student_count', 'created_at')
    search_fields = ('name', 'intake')
    list_filter = ('intake',)
    ordering = ('name',)
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('building', 'hall', 'capacity', 'created_at')
    search_fields = ('building', 'hall')
    ordering = ('building', 'hall')

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('lecturer_id', 'fullname', 'email', 'created_at')
    search_fields = ('lecturer_id', 'fullname', 'email')
    ordering = ('lecturer_id',)
    readonly_fields = ('user', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Lecturer Information', {
            'fields': ('lecturer_id', 'fullname', 'email')
        }),
        ('System Information', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        When saving a lecturer, automatically create User and UserProfile.
        Default password is the lecturer_id.
        """
        super().save_model(request, obj, form, change)
        if obj.user:
            # Notify admin about the default password
            self.message_user(
                request,
                f"Lecturer '{obj.fullname}' created. Username: {obj.lecturer_id}, Default Password: {obj.lecturer_id} (User should change this)"
            )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'fullname', 'email', 'group', 'created_at')
    search_fields = ('student_id', 'fullname', 'email', 'group__name')
    list_filter = ('group',)
    ordering = ('student_id',)
    readonly_fields = ('user', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'fullname', 'email', 'group')
        }),
        ('System Information', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        When saving a student, automatically create User and UserProfile.
        Default password is the student_id.
        """
        super().save_model(request, obj, form, change)
        if obj.user:
            # Notify admin about the default password
            self.message_user(
                request,
                f"Student '{obj.fullname}' created. Username: {obj.student_id}, Default Password: {obj.student_id} (User should change this)"
            )

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ('user_type',)

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_user_type')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__user_type')
    
    def get_user_type(self, obj):
        return obj.userprofile.get_user_type_display() if hasattr(obj, 'userprofile') else '-'
    get_user_type.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'starting_time', 'ending_time', 'lecturer', 'room', 'lesson_type')
    list_filter = ('lesson_type', 'date', 'lecturer', 'course')
    search_fields = ('course__title', 'course__course_code', 'lecturer__fullname', 'room__building', 'room__hall')
    date_hierarchy = 'date'
    filter_horizontal = ('groups',)
    ordering = ('-date', '-starting_time')
    
    def delete_model(self, request, obj):
        """Override to create notification before deletion"""
        from .utils import create_lesson_notification
        # Create notification BEFORE deleting
        create_lesson_notification(obj, 'CANCELLATION')
        # Now delete the lesson
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Handle bulk delete - create notifications before deletion"""
        from .utils import create_lesson_notification
        # Create notifications for all lessons BEFORE deleting
        for obj in queryset:
            create_lesson_notification(obj, 'CANCELLATION')
        # Now delete all lessons
        super().delete_queryset(request, queryset)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'lesson', 'is_sent', 'created_at')
    list_filter = ('message_type', 'is_sent', 'created_at')
    search_fields = ('message_text', 'lesson__course__title', 'lesson__course__course_code')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)