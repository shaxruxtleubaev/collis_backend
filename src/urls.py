# --- In src/urls.py (The main project urls.py) ---

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Django Admin with Jazzmin
    path('admin/', admin.site.urls),
    
    # ------------------
    # API AUTHENTICATION
    # ------------------
    
    # Get a new Access and Refresh Token pair (Login)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Renew the Access Token using the Refresh Token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ------------------
    # API DOCUMENTATION (Swagger UI)
    # ------------------
    
    # Serves the OpenAPI schema file
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Serves the Swagger UI interface
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ------------------
    # CORE APP ENDPOINTS
    # ------------------
    
    path('api/', include('timetable.urls')),
]