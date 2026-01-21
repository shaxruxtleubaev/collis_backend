from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user_type_choices = [
        ('ADMIN', 'Admin'),
        ('LECTURER', 'Lecturer'),
        ('STUDENT', 'Student'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=10, choices=user_type_choices)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class Course(models.Model):
    title = models.CharField(max_length=255)
    course_code = models.CharField(max_length=20, unique=True)
    credits = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_code} - {self.title}"

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True)
    intake = models.CharField(max_length=50, help_text="Program intake (e.g., FIT, FIS, FIM)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.intake})"

class Room(models.Model):
    building = models.CharField(max_length=100)
    hall = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['building', 'hall']

    def __str__(self):
        return f"{self.building} - {self.hall}"

class Lecturer(models.Model):
    lecturer_id = models.CharField(max_length=50, unique=True, primary_key=True)
    fullname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.lecturer_id} - {self.fullname}"
    
    def save(self, *args, **kwargs):
        # Auto-create User and UserProfile only if this is a new lecturer
        if not self.pk and not self.user:  # Check if this is a new instance
            # Check if user already exists with this username
            if not User.objects.filter(username=self.lecturer_id).exists():
                # Create User with lecturer_id as username
                user = User.objects.create_user(
                    username=self.lecturer_id,
                    email=self.email,
                    password=self.lecturer_id  # Default password is lecturer_id
                )
                user.first_name = self.fullname.split()[0] if self.fullname else ''
                user.last_name = ' '.join(self.fullname.split()[1:]) if len(self.fullname.split()) > 1 else ''
                user.save()
                
                # Create UserProfile
                UserProfile.objects.create(user=user, user_type='LECTURER')
                
                self.user = user
        
        super().save(*args, **kwargs)

class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True, primary_key=True)
    fullname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_id} - {self.fullname}"
    
    def save(self, *args, **kwargs):
        # Auto-create User and UserProfile only if this is a new student
        if not self.pk and not self.user:  # Check if this is a new instance
            # Check if user already exists with this username
            if not User.objects.filter(username=self.student_id).exists():
                # Create User with student_id as username
                user = User.objects.create_user(
                    username=self.student_id,
                    email=self.email,
                    password=self.student_id  # Default password is student_id
                )
                user.first_name = self.fullname.split()[0] if self.fullname else ''
                user.last_name = ' '.join(self.fullname.split()[1:]) if len(self.fullname.split()) > 1 else ''
                user.save()
                
                # Create UserProfile
                UserProfile.objects.create(user=user, user_type='STUDENT')
                
                self.user = user
        
        super().save(*args, **kwargs)

class Lesson(models.Model):
    type_choices = [
        ('LECTURE', 'Lecture'), 
        ('TUTORIAL', 'Tutorial'), 
        ('LAB', 'Lab')
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    groups = models.ManyToManyField(Group, related_name='lessons')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='lessons')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='lessons')
    lesson_type = models.CharField(max_length=10, choices=type_choices)
    date = models.DateField()
    starting_time = models.TimeField()
    ending_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['date', 'starting_time']),
            models.Index(fields=['date', 'lecturer']),
            models.Index(fields=['date', 'room']),
        ]
        ordering = ['date', 'starting_time']

    def __str__(self):
        return f"{self.course.course_code} - {self.date} {self.starting_time} ({self.lesson_type})"

class Notification(models.Model):
    type_choices = [
        ('ANNOUNCEMENT', 'Announcement'), 
        ('RESCHEDULE', 'Reschedule'), 
        ('CANCELLATION', 'Cancellation')
    ]
    # Changed to SET_NULL so notifications are kept when lesson is deleted
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, related_name='notifications', null=True, blank=True)
    
    # Store lesson details in case lesson is deleted
    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=255)
    lesson_date = models.DateField()
    lesson_time = models.TimeField()
    group_names = models.CharField(max_length=255)
    
    message_type = models.CharField(max_length=20, choices=type_choices)
    message_text = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.message_type} - {self.course_code} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"