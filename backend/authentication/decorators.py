# backend/authentication/decorators.py
from functools import wraps
from rest_framework.exceptions import PermissionDenied
from authentication.models import Role

def enforce_rbac_hierarchy(minimum_role_name: str):
    """
    Strict server-side validation decorator for API endpoints.
    Evaluates the user's role tree depth against the required base node name.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise PermissionDenied("Authentication mapping state missing.")
            
            user_role = request.user.role
            if not user_role:
                raise PermissionDenied("Access Denied: Operational role context omitted.")

            # Short-circuit if the assigned role is an exact match
            if user_role.name.upper() == minimum_role_name.upper():
                return view_func(request, *args, **kwargs)

            # Traverse the hierarchical parent nodes upward
            has_access = False
            current_node = user_role
            while current_node.parent is not None:
                if current_node.parent.name.upper() == minimum_role_name.upper():
                    has_access = True
                    break
                current_node = current_node.parent

            if not has_access:
                raise PermissionDenied("Access Denied: Insufficient hierarchical privileges.")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator