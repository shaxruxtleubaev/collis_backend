from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'groups', views.GroupViewSet, basename='group')
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'profiles', views.UserProfileViewSet, basename='profile')
router.register(r'lecturers', views.LecturerViewSet, basename='lecturer')
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]