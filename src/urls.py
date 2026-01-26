from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
# REMOVE this import: from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # REMOVED: path('api/login/', obtain_auth_token, name='api_login'),
    # The custom token endpoint is now at /api/token/ via timetable.urls
    
    # API DOCUMENTATION (Swagger UI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # CORE APP ENDPOINTS (includes /api/token/)
    path('api/', include('timetable.urls')),
]