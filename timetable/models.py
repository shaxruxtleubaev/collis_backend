from django.db import models
from django.contrib.auth.models import User

# --- Core Tables ---

class Room(models.Model):
    """
    Represents a specific physical location for lessons.
    Used for conflict detection and utilization analytics.
    institution_id field removed.
    """
    building = models.CharField(max_length=255)
    hall = models.CharField(max_length=255)
    capacity = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('building', 'hall')
        
    def __str__(self):
        return f'{self.building} - {self.hall}'

class Course(models.Model):
    """
    Academic course details.
    """
    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=255, unique=True)
    credits = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.course_code}: {self.title}'

class Group(models.Model):
    """
    Student cohorts (e.g., SE401, BC210).
    """
    name = models.CharField(max_length=255, unique=True)
    intake = models.CharField(max_length=255)
    
    def __str__(self):
        return f'{self.name} ({self.intake})'

# --- User Tables ---

class UserProfile(models.Model):
    """
    Extends Django's built-in User model to add custom roles.
    institution field removed.
    """
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('LECTURER', 'Lecturer'),
        ('STUDENT', 'Student'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=255, choices=USER_TYPE_CHOICES)
    
    def __str__(self):
        return f'{self.user.username} - {self.user_type}'

class Lecturer(models.Model):
    """
    Details specific to a Lecturer.
    institution field removed.
    """
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=255)
    
    def __str__(self):
        return self.fullname

class Student(models.Model):
    """
    Details specific to a Student.
    institution field removed.
    """
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=255)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.fullname} ({self.group.name})'

# --- Scheduling Tables ---

class Lesson(models.Model):
    """
    Represents a single scheduled class instance.
    institution field removed.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    
    LESSON_TYPE_CHOICES = (
        ('LECTURE', 'Lecture'),
        ('PRACTICAL', 'Practical'),
    )
    
    lesson_type = models.CharField(max_length=255, choices=LESSON_TYPE_CHOICES, help_text='Lecture/Practical')
    date = models.DateField()
    starting_time = models.TimeField()
    ending_time = models.TimeField()
    
    def __str__(self):
        return f'{self.course.course_code} on {self.date} at {self.starting_time}'

# --- Notifications / Real-time Tables ---

class Device(models.Model):
    """
    Stores push notification tokens for mobile devices.
    institution field removed.
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    
    PLATFORM_CHOICES = (
        ('ANDROID', 'Android'),
        ('IOS', 'iOS'),
        ('WEB', 'Web Browser'),
    )
    
    platform = models.CharField(max_length=255, choices=PLATFORM_CHOICES)
    registration_id = models.CharField(max_length=255, unique=True, help_text='FCM/APNS device token')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user_profile.user.username} - {self.platform}'

class Notification(models.Model):
    """
    History of schedule changes/alerts sent to users.
    institution field removed.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    
    MESSAGE_TYPE_CHOICES = (
        ('RESCHEDULE', 'Reschedule'),
        ('CANCELLATION', 'Cancellation'),
        ('ROOM_CHANGE', 'Room Change'),
        ('ANNOUNCEMENT', 'General Announcement'),
    )
    
    message_type = models.CharField(max_length=255, choices=MESSAGE_TYPE_CHOICES)
    message_text = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.message_type}: {self.message_text[:30]}...'