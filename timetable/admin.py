from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from .models import (
    Course, Group, Room,
    Lecturer, Student, UserProfile,
    Lesson, Notification
)
from .utils import create_lesson_notification 
import secrets
import string

def generate_secure_password(length=12):
    """Generate a random secure password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

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
    list_display = ('lecturer_id', 'fullname', 'email', 'created_at', 'user_status')
    search_fields = ('lecturer_id', 'fullname', 'email')
    ordering = ('lecturer_id',)
    readonly_fields = ('user', 'created_at', 'updated_at', 'password_help_text')
    
    fieldsets = (
        ('Lecturer Information', {
            'fields': ('lecturer_id', 'fullname', 'email')
        }),
        ('System Information', {
            'fields': ('user', 'password_help_text', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_status(self, obj):
        """Display user status in list view"""
        if obj.user:
            return format_html(
                '<span style="color: green;">✓ User Created</span>'
            )
        return format_html(
            '<span style="color: orange;">⚠ No User</span>'
        )
    user_status.short_description = 'User Status'
    
    def password_help_text(self, obj):
        """Display password help text in detail view"""
        if obj.user:
            return format_html(
                '<div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">'
                '<strong>User Account Status:</strong> Created<br>'
                '<em>Password was set during creation and is not stored in plain text. '
                'To reset password, go to the User admin page.</em>'
                '</div>'
            )
        return format_html(
            '<div style="background: #fff3cd; padding: 10px; border-radius: 5px;">'
            '<strong>Note:</strong> When you save this lecturer, a user account will be created '
            'with a random password. The password will be shown <strong>only once</strong> '
            'in the success message at the top of the page.'
            '</div>'
        )
    password_help_text.short_description = 'Password Information'
    
    def save_model(self, request, obj, form, change):
        """
        When saving a lecturer, automatically create User and UserProfile.
        Generate secure random password.
        """
        password = generate_secure_password()
        user_created = False
        show_password = False
        
        # Create User if it doesn't exist
        if not obj.user:
            # Check if user already exists with this username
            try:
                existing_user = User.objects.get(username=obj.lecturer_id)
                # User exists, link it to this lecturer
                obj.user = existing_user
                
                # Update user email and name if different
                if existing_user.email != obj.email:
                    existing_user.email = obj.email
                    existing_user.save()
                
                message = (
                    f"Lecturer '{obj.fullname}' linked to existing user. "
                    f"Username: {obj.lecturer_id}"
                )
                
            except User.DoesNotExist:
                # Create new User with lecturer_id as username
                user = User.objects.create_user(
                    username=obj.lecturer_id,
                    email=obj.email,
                    password=password
                )
                
                # Set lecturer as staff (can access admin)
                user.is_staff = True
                user.first_name = obj.fullname.split()[0] if obj.fullname else ''
                user.last_name = ' '.join(obj.fullname.split()[1:]) if len(obj.fullname.split()) > 1 else ''
                user.save()
                
                # Give lecturer permissions to manage their own lessons
                lesson_content_type = ContentType.objects.get_for_model(Lesson)
                lesson_permissions = Permission.objects.filter(content_type=lesson_content_type)
                
                # Add specific permissions: view, add, change, delete lessons
                for perm in lesson_permissions:
                    user.user_permissions.add(perm)
                
                # Create UserProfile if it doesn't exist
                if not hasattr(user, 'userprofile'):
                    UserProfile.objects.create(user=user, user_type='LECTURER')
                else:
                    # Update existing profile
                    user.userprofile.user_type = 'LECTURER'
                    user.userprofile.save()
                
                obj.user = user
                user_created = True
                show_password = True
                message = (
                    f"Lecturer '{obj.fullname}' created. "
                    f"Username: <strong>{obj.lecturer_id}</strong>, "
                    f"Password: <strong>{password}</strong><br>"
                    f"<em style='color: red;'>Copy this password now! It won't be shown again.</em>"
                )
        else:
            # Lecturer already has a user, just update
            message = f"Lecturer '{obj.fullname}' updated."
        
        # Save the lecturer
        super().save_model(request, obj, form, change)
        
        # Show appropriate message
        if show_password:
            self.message_user(request, format_html(message), extra_tags='safe')
        else:
            self.message_user(request, message)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'fullname', 'email', 'group', 'created_at', 'user_status')
    search_fields = ('student_id', 'fullname', 'email', 'group__name')
    list_filter = ('group',)
    ordering = ('student_id',)
    readonly_fields = ('user', 'created_at', 'updated_at', 'password_help_text')
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_id', 'fullname', 'email', 'group')
        }),
        ('System Information', {
            'fields': ('user', 'password_help_text', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_status(self, obj):
        """Display user status in list view"""
        if obj.user:
            return format_html(
                '<span style="color: green;">✓ User Created</span>'
            )
        return format_html(
            '<span style="color: orange;">⚠ No User</span>'
        )
    user_status.short_description = 'User Status'
    
    def password_help_text(self, obj):
        """Display password help text in detail view"""
        if obj.user:
            return format_html(
                '<div style="background: #f0f0f0; padding: 10px; border-radius: 5px;">'
                '<strong>User Account Status:</strong> Created<br>'
                '<em>Password was set during creation and is not stored in plain text. '
                'To reset password, go to the User admin page.</em>'
                '</div>'
            )
        return format_html(
            '<div style="background: #fff3cd; padding: 10px; border-radius: 5px;">'
            '<strong>Note:</strong> When you save this student, a user account will be created '
            'with a random password. The password will be shown <strong>only once</strong> '
            'in the success message at the top of the page.'
            '</div>'
        )
    password_help_text.short_description = 'Password Information'
    
    def save_model(self, request, obj, form, change):
        """
        When saving a student, automatically create User and UserProfile.
        Generate secure random password.
        """
        password = generate_secure_password()
        user_created = False
        show_password = False
        
        # Create User if it doesn't exist
        if not obj.user:
            # Check if user already exists with this username
            try:
                existing_user = User.objects.get(username=obj.student_id)
                # User exists, link it to this student
                obj.user = existing_user
                
                # Update user email if different
                if existing_user.email != obj.email:
                    existing_user.email = obj.email
                    existing_user.save()
                
                message = (
                    f"Student '{obj.fullname}' linked to existing user. "
                    f"Username: {obj.student_id}"
                )
                
            except User.DoesNotExist:
                # Create User with student_id as username
                user = User.objects.create_user(
                    username=obj.student_id,
                    email=obj.email,
                    password=password
                )
                
                # Student is NOT staff (cannot access admin)
                user.is_staff = False
                user.first_name = obj.fullname.split()[0] if obj.fullname else ''
                user.last_name = ' '.join(obj.fullname.split()[1:]) if len(obj.fullname.split()) > 1 else ''
                user.save()
                
                # Create UserProfile if it doesn't exist
                if not hasattr(user, 'userprofile'):
                    UserProfile.objects.create(user=user, user_type='STUDENT')
                else:
                    # Update existing profile
                    user.userprofile.user_type = 'STUDENT'
                    user.userprofile.save()
                
                obj.user = user
                user_created = True
                show_password = True
                message = (
                    f"Student '{obj.fullname}' created. "
                    f"Username: <strong>{obj.student_id}</strong>, "
                    f"Password: <strong>{password}</strong><br>"
                    f"<em style='color: red;'>Copy this password now! It won't be shown again.</em>"
                )
        else:
            # Student already has a user, just update
            message = f"Student '{obj.fullname}' updated."
        
        # Save the student
        super().save_model(request, obj, form, change)
        
        # Show appropriate message
        if show_password:
            self.message_user(request, format_html(message), extra_tags='safe')
        else:
            self.message_user(request, message)

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
    
    def get_queryset(self, request):
        """Limit lessons shown to lecturers (only their own lessons)"""
        qs = super().get_queryset(request)
        
        # If user is a lecturer, only show their lessons
        if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
            if request.user.userprofile.user_type == 'LECTURER' and hasattr(request.user, 'lecturer'):
                return qs.filter(lecturer=request.user.lecturer)
        
        return qs
    
    def delete_model(self, request, obj):
        """Override to create notification before deletion"""
        from .utils import create_lesson_notification
        # Create notification BEFORE deleting
        create_lesson_notification(obj, 'CANCELLATION')
        # Now delete the lesson (notifications stay in database)
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Handle bulk delete - create notifications before deletion"""
        from .utils import create_lesson_notification
        # Create notifications for all lessons BEFORE deleting
        for obj in queryset:
            create_lesson_notification(obj, 'CANCELLATION')
        # Now delete all lessons (notifications stay in database)
        super().delete_queryset(request, queryset)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message_type', 'lesson', 'is_sent', 'created_at')
    list_filter = ('message_type', 'is_sent', 'created_at')
    search_fields = ('message_text', 'lesson__course__title', 'lesson__course__course_code')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)