from rest_framework.permissions import BasePermission

class IsSystemAdmin(BasePermission):
    """
    Strict Zero-Trust Authorization Guard.
    Ensures the request user is authenticated and explicitly tied to the 'Admin' Role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role and 
            request.user.role.name == 'Admin'
        )