from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate

class CustomObtainAuthToken(ObtainAuthToken):
    """
    Custom token authentication that works with student/lecturer IDs
    """
    
    def post(self, request, *args, **kwargs):
        # Get username and password from request
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate using our custom backend
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user profile info
            profile_data = {}
            if hasattr(user, 'userprofile'):
                profile_data = {
                    'user_type': user.userprofile.user_type,
                    'user_type_display': user.userprofile.get_user_type_display(),
                    'fullname': user.get_full_name() or user.username,
                }
                
                # Add specific IDs
                if user.userprofile.user_type == 'STUDENT' and hasattr(user, 'student'):
                    profile_data['student_id'] = user.student.student_id
                elif user.userprofile.user_type == 'LECTURER' and hasattr(user, 'lecturer'):
                    profile_data['lecturer_id'] = user.lecturer.lecturer_id
            
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                **profile_data
            })
        
        return Response(
            {'error': 'Invalid credentials'}, 
            status=400
        )