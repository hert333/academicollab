from functools import wraps
from django.core.exceptions import PermissionDenied
from authentication.roles import RoleLevel, has_minimum_role

def enforce_rbac_hierarchy(minimum_role: RoleLevel):
    """
    Strict server-side validation decorator. Evaluates the request profile attribute 
    against integer role levels prior to executing view logic.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Assumes your user profile model injects a 'role_level' integer field
            user_profile = getattr(request.user, 'profile', None)
            
            if not request.user.is_authenticated or user_profile is None:
                raise PermissionDenied("Authentication mapping state missing.")
            
            if not has_minimum_role(user_profile.role_level, minimum_role):
                raise PermissionDenied("Access Denied: Insufficient hierarchical privileges.")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator