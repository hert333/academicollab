# backend/authentication/permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from authentication.models import Role

def is_system_admin(user) -> bool:
    """
    Absolute security evaluation to identify top-tier administrative tokens.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role:
        if user.role.name.upper() in ['ADMIN', 'SYSTEM ADMINISTRATOR', 'SYSTEMADMIN']:
            return True
    return False

class IsMinimumHierarchicalRole(BasePermission):
    """
    Dynamic Data-Driven DRF Authorization Engine for views.
    """
    def has_permission(self, request, view):
        required_role_name = getattr(view, 'required_minimum_role', None)
        if not required_role_name:
            return True  

        user = request.user
        if is_system_admin(user):
            return True

        if not user or not user.role:
            raise PermissionDenied("Access Denied: Missing operational role context.")

        try:
            target_base_role = Role.objects.get(name__iexact=required_role_name)
            allowed_role_ids = target_base_role.get_ancestor_ids()

            if user.role.id in allowed_role_ids or user.role.id == target_base_role.id:
                return True
        except Role.DoesNotExist:
            raise PermissionDenied(
                f"Security Configuration Error: Clearance node '{required_role_name}' does not exist."
            )

        return False