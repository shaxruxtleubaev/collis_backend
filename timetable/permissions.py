from rest_framework import permissions

class IsInstitutionAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users to create/update objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any user (handled by IsAuthenticated)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions (POST, PUT, DELETE) are only allowed to users with ADMIN role
        return hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'ADMIN'

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow Admins/Lecturers to modify, but Students only to read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(request.user, 'userprofile'):
            user_type = request.user.userprofile.user_type
            return user_type in ['ADMIN', 'LECTURER']
        
        return False