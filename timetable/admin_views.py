from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect

class CustomAdminLoginView(LoginView):
    """Custom admin login that redirects non-staff users to frontend"""
    template_name = 'admin/login.html'
    authentication_form = AuthenticationForm
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already authenticated
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('/')  # Redirect to frontend
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redirect based on user type"""
        user = self.request.user
        if user.is_staff:
            return '/admin/'
        else:
            return '/'  # Frontend