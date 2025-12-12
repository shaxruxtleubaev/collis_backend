# --- Update timetable/urls.py ---

from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

router = DefaultRouter()

# Foundation and Configuration Endpoints
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'groups', views.GroupViewSet, basename='group')
router.register(r'rooms', views.RoomViewSet, basename='room')

# Core Scheduling Endpoint
router.register(r'lessons', views.LessonViewSet, basename='lesson')

# User Endpoints
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'lecturers', views.LecturerViewSet, basename='lecturer')
router.register(r'students', views.StudentViewSet, basename='student')

# Notification Endpoints (NEW)
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'notifications', views.NotificationViewSet, basename='notification')


urlpatterns = [
    # Custom registration endpoint
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
] + router.urls