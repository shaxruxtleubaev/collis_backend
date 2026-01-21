from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Student, Lecturer

class StudentLecturerAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with:
    - Username (default Django behavior)
    - Student ID (for students)
    - Lecturer ID (for lecturers)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        user = None
        
        # Try to find user by username first (default behavior)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Try to find by student_id
            try:
                student = Student.objects.get(student_id=username)
                user = student.user
            except Student.DoesNotExist:
                # Try to find by lecturer_id
                try:
                    lecturer = Lecturer.objects.get(lecturer_id=username)
                    user = lecturer.user
                except Lecturer.DoesNotExist:
                    return None
        
        # Check password
        if user and user.check_password(password):
            return user
        
        return None