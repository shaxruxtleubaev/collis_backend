from rest_framework import viewsets
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    CourseSerializer, GroupSerializer, RoomSerializer,
    LecturerSerializer, StudentSerializer, UserProfileSerializer,
    LessonSerializer, UserRegistrationSerializer,
    DeviceSerializer, NotificationSerializer
)
from .models import (
    Course, Group, Room,
    Lecturer, Student, Lesson,
    UserProfile, Device, Notification
)
from .permissions import IsInstitutionAdmin, IsStaffOrReadOnly
from .utils import create_lesson_notification


# --- Foundation ViewSets ---

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Courses to be viewed or edited.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Room management.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

# --- Scheduling ViewSet ---

class LessonViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Lesson schedules.
    Notification logic is now handled by Django Signals.
    """
    queryset = Lesson.objects.all().select_related('course', 'lecturer', 'group', 'room')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Apply contextual filter for personalized schedules
        if self.request.user.is_authenticated and hasattr(self.request.user, 'userprofile'):
            profile = self.request.user.userprofile
            
            if profile.user_type == 'STUDENT':
                try:
                    student = profile.student
                    queryset = queryset.filter(group=student.group)
                except Student.DoesNotExist:
                    return queryset.none()
            
            elif profile.user_type == 'LECTURER':
                try:
                    lecturer = profile.lecturer
                    queryset = queryset.filter(lecturer=lecturer)
                except Lecturer.DoesNotExist:
                    return queryset.none()
        
        # Order by date and time
        return queryset.order_by('date', 'starting_time')


# --- User ViewSets and Registration ---

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Allows authenticated users to view profiles.
    """
    queryset = UserProfile.objects.all().select_related('user')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

class LecturerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Allows viewing of Lecturers.
    """
    queryset = Lecturer.objects.all().select_related('user_profile')
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Allows viewing of Students.
    """
    queryset = Student.objects.all().select_related('user_profile', 'group')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

class UserRegistrationView(generics.CreateAPIView):
    """
    Custom endpoint for Student and Lecturer registration.
    No authentication required.
    """
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Return a success message
        return Response(
            {"message": f"{serializer.validated_data['user_type']} registered successfully.", "username": user.username}, 
            status=status.HTTP_201_CREATED
        )

# --- Notification ViewSets ---

class DeviceViewSet(viewsets.ModelViewSet):
    """
    Allows users to register their mobile devices for push notifications.
    Each authenticated user manages their own devices.
    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    # Users can only see/manage their own devices
    def get_queryset(self):
        return self.queryset.filter(user_profile=self.request.user.userprofile)

    def perform_create(self, serializer):
        # Automatically link the device to the current user's profile
        serializer.save(user_profile=self.request.user.userprofile)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Allows authenticated users to view their notification history.
    """
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter notifications relevant to the current user (Lecturer or Student)
        user_profile = self.request.user.userprofile
        
        # Base queryset: all notifications, ordered by creation time
        queryset = self.queryset

        if user_profile.user_type == 'STUDENT':
            # Students get notifications for lessons assigned to their group
            try:
                group = user_profile.student.group
                return queryset.filter(lesson__group=group)
            except Student.DoesNotExist:
                return queryset.none()

        elif user_profile.user_type == 'LECTURER':
            # Lecturers get notifications for lessons they are teaching
            try:
                lecturer = user_profile.lecturer
                return queryset.filter(lesson__lecturer=lecturer)
            except Lecturer.DoesNotExist:
                return queryset.none()
        
        # Admin sees all notifications (no filtering needed on the base queryset)
        return queryset