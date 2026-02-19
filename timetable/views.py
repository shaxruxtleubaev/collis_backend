from rest_framework import viewsets, generics, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .serializers import (
    CourseSerializer, GroupSerializer, RoomSerializer,
    LecturerSerializer, StudentSerializer, UserProfileSerializer,
    LessonSerializer, NotificationSerializer, ChangePasswordSerializer
)
from .models import (
    Course, Group, Room,
    Lecturer, Student, Lesson,
    UserProfile, Notification
)
from .permissions import IsInstitutionAdmin, IsStaffOrReadOnly

# --- Foundation ViewSets ---

@extend_schema_view(
    list=extend_schema(description="List all courses"),
    create=extend_schema(description="Create a new course (Admin only)"),
    retrieve=extend_schema(description="Get course details"),
    update=extend_schema(description="Update a course (Admin only)"),
    destroy=extend_schema(description="Delete a course (Admin only)")
)
class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing courses.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'course_code']
    ordering_fields = ['course_code', 'title', 'credits']
    ordering = ['course_code']

@extend_schema_view(
    list=extend_schema(description="List all groups"),
    create=extend_schema(description="Create a new group (Admin only)"),
    retrieve=extend_schema(description="Get group details"),
    update=extend_schema(description="Update a group (Admin only)"),
    destroy=extend_schema(description="Delete a group (Admin only)")
)
class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing student groups.
    """
    queryset = Group.objects.prefetch_related('students')
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['intake']
    search_fields = ['name', 'intake']
    ordering_fields = ['name', 'intake']
    ordering = ['name']

@extend_schema_view(
    list=extend_schema(description="List all rooms"),
    create=extend_schema(description="Create a new room (Admin only)"),
    retrieve=extend_schema(description="Get room details"),
    update=extend_schema(description="Update a room (Admin only)"),
    destroy=extend_schema(description="Delete a room (Admin only)")
)
class RoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing rooms.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['building']
    search_fields = ['building', 'hall']
    ordering_fields = ['building', 'hall', 'capacity']
    ordering = ['building', 'hall']

# --- Scheduling ViewSet ---

@extend_schema_view(
    list=extend_schema(
        description="List lessons. Students see their group's lessons, lecturers see their lessons, admins see all.",
        parameters=[
            OpenApiParameter(name='date', description='Filter by date (YYYY-MM-DD)', required=False, type=str),
            OpenApiParameter(name='lesson_type', description='Filter by lesson type', required=False, type=str),
        ]
    ),
    create=extend_schema(description="Create a new lesson (Admin and Lecturer only)"),
    retrieve=extend_schema(description="Get lesson details"),
    update=extend_schema(description="Update a lesson (Admin and Lecturer only)"),
    destroy=extend_schema(description="Delete a lesson (Admin and Lecturer only)")
)
class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lessons.
    
    Personalized filtering:
    - Students: See only their group's lessons
    - Lecturers: See only their lessons
    - Admins: See all lessons
    """
    queryset = Lesson.objects.select_related('course', 'lecturer', 'room').prefetch_related('groups')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'lesson_type', 'lecturer', 'course', 'room']
    search_fields = ['course__title', 'course__course_code', 'lecturer__fullname']
    ordering_fields = ['date', 'starting_time']
    ordering = ['date', 'starting_time']

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated and hasattr(self.request.user, 'userprofile'):
            profile = self.request.user.userprofile
            
            # Filter for Students
            if profile.user_type == 'STUDENT' and hasattr(self.request.user, 'student'):
                return queryset.filter(groups=self.request.user.student.group)
            
            # Filter for Lecturers
            elif profile.user_type == 'LECTURER' and hasattr(self.request.user, 'lecturer'):
                return queryset.filter(lecturer=self.request.user.lecturer)
        
        return queryset
    
    def perform_destroy(self, instance):
        """Override to create notification before deletion"""
        from .utils import create_lesson_notification
        # Create cancellation notification BEFORE deleting
        create_lesson_notification(instance, 'CANCELLATION')
        # Now delete the lesson
        super().perform_destroy(instance)

# --- User ViewSets ---

@extend_schema_view(
    list=extend_schema(description="List all user profiles"),
    retrieve=extend_schema(description="Get user profile details"),
)
class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user profiles.
    """
    queryset = UserProfile.objects.select_related('user')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        description="Get the currently authenticated user's profile",
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user.userprofile)
        return Response(serializer.data)
    
    @extend_schema(
        description="Change user password",
        request=ChangePasswordSerializer,
        responses={200: {"description": "Password changed successfully"}}
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change password for current user"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(description="List all lecturers"),
    retrieve=extend_schema(description="Get lecturer details"),
)
class LecturerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing lecturers.
    """
    queryset = Lecturer.objects.all()
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['lecturer_id', 'fullname', 'email']
    ordering_fields = ['lecturer_id', 'fullname']
    ordering = ['lecturer_id']

    def get_permissions(self):
        """
        Override to allow lecturers to modify only their own lessons.
        """
        permission_classes = [IsAuthenticated]
        
        # For write operations (POST, PUT, PATCH, DELETE)
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes.append(IsStaffOrReadOnly)
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated and hasattr(self.request.user, 'userprofile'):
            profile = self.request.user.userprofile
            
            # Filter for Students
            if profile.user_type == 'STUDENT' and hasattr(self.request.user, 'student'):
                return queryset.filter(groups=self.request.user.student.group)
            
            # Filter for Lecturers
            elif profile.user_type == 'LECTURER' and hasattr(self.request.user, 'lecturer'):
                return queryset.filter(lecturer=self.request.user.lecturer)
        
        return queryset
    
    def perform_create(self, serializer):
        """Lecturers can only create lessons for themselves"""
        if (hasattr(self.request.user, 'userprofile') and 
            self.request.user.userprofile.user_type == 'LECTURER'):
            # Ensure lecturer is set to current user's lecturer
            serializer.save(lecturer=self.request.user.lecturer)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Lecturers can only update their own lessons"""
        if (hasattr(self.request.user, 'userprofile') and 
            self.request.user.userprofile.user_type == 'LECTURER'):
            # Ensure lecturer cannot be changed by lecturer
            instance = self.get_object()
            if instance.lecturer != self.request.user.lecturer:
                raise PermissionDenied("You can only update your own lessons.")
            serializer.save()
        else:
            serializer.save()
    
    def perform_destroy(self, instance):
        """Lecturers can only delete their own lessons"""
        if (hasattr(self.request.user, 'userprofile') and 
            self.request.user.userprofile.user_type == 'LECTURER'):
            if instance.lecturer != self.request.user.lecturer:
                raise PermissionDenied("You can only delete your own lessons.")
        
        from .utils import create_lesson_notification
        # Create cancellation notification BEFORE deleting
        create_lesson_notification(instance, 'CANCELLATION')
        # Now delete the lesson
        super().perform_destroy(instance)

@extend_schema_view(
    list=extend_schema(description="List all students"),
    retrieve=extend_schema(description="Get student details"),
)
class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing students.
    """
    queryset = Student.objects.select_related('group')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['group']
    search_fields = ['student_id', 'fullname', 'email']
    ordering_fields = ['student_id', 'fullname']
    ordering = ['student_id']

# --- Notification ViewSet ---

@extend_schema_view(
    list=extend_schema(
        description="List notifications. Students see notifications for their group's lessons, lecturers for their lessons."
    ),
    retrieve=extend_schema(description="Get notification details"),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications.
    
    Personalized filtering:
    - Students: See notifications for their group's lessons
    - Lecturers: See notifications for their lessons
    - Admins: See all notifications
    """
    queryset = Notification.objects.select_related('lesson__course', 'lesson__lecturer', 'lesson__room').prefetch_related('lesson__groups')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['message_type', 'is_sent']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return all notifications for authenticated users"""
        # All authenticated users see all notifications
        return self.queryset
    
    @extend_schema(
        description="Mark a notification as read for the current user",
        responses={200: {"description": "Notification marked as read"}}
    )
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read for current user"""
        from .models import NotificationRead
        notification = self.get_object()
        
        # Create or get NotificationRead entry
        read_entry, created = NotificationRead.objects.get_or_create(
            notification=notification,
            user=request.user
        )
        
        message = "Notification marked as read" if created else "Notification already marked as read"
        return Response(
            {'message': message, 'read_at': read_entry.read_at},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="Get count of unread notifications for current user",
        responses={200: {"type": "object", "properties": {"unread_count": {"type": "integer"}}}}
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count for current user"""
        from .models import NotificationRead
        
        # Get all relevant notifications for this user
        queryset = self.get_queryset()
        
        # If student, filter by their group
        if (hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type == 'STUDENT' and 
            hasattr(request.user, 'student')):
            # Filter notifications for student's group
            group_name = request.user.student.group.name
            queryset = queryset.extra(
                where=[f"group_names LIKE %s"],
                params=[f"%{group_name}%"]
            )
        
        # Count unread (not in NotificationRead table)
        all_notification_ids = set(queryset.values_list('id', flat=True))
        read_notification_ids = set(
            NotificationRead.objects.filter(user=request.user).values_list('notification_id', flat=True)
        )
        unread_ids = all_notification_ids - read_notification_ids
        
        return Response(
            {'unread_count': len(unread_ids)},
            status=status.HTTP_200_OK
        )