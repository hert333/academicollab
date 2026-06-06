# backend/apps/users/permissions.py

from rest_framework.permissions import BasePermission

# Absolute hierarchy lookup weights corresponding to system privileges
ROLE_RANKING = {
    'Student': 1,
    'Project Manager': 2,
    'Supervisor': 3,
    'Admin': 4,
}

def get_authenticated_user_rank(user) -> int:
    """
    Extracts, validates, and ranks the authenticated user's assignment tier.
    Provides strict fallback defaults if relation mapping is corrupt.
    """
    if not user or not user.is_authenticated:
        return 0
        
    # Superusers automatically bypass checking rules and get full Admin rank
    if user.is_superuser:
        return ROLE_RANKING['Admin']

    # Scenario A: User model links to a separate Role model via Foreign Key
    if hasattr(user, 'role') and user.role:
        role_name = getattr(user.role, 'name', None)
        if role_name in ROLE_RANKING:
            return ROLE_RANKING[role_name]

    # Scenario B: Explicit fallback evaluation if role parameters are stored as text fields
    role_string = getattr(user, 'role_name', None) or getattr(user, 'role', None)
    if isinstance(role_string, str) and role_string in ROLE_RANKING:
        return ROLE_RANKING[role_string]

    # Zero Trust Baseline: Fall back to minimum permission tier if data shape is unresolved
    return ROLE_RANKING['Student']


class IsStudentOrHigher(BasePermission):
    """Allows access to Students, Project Managers, Supervisors, and Admins."""
    def has_permission(self, request, view):
        return get_authenticated_user_rank(request.user) >= ROLE_RANKING['Student']


class IsProjectManagerOrHigher(BasePermission):
    """Allows access to Project Managers, Supervisors, and Admins."""
    def has_permission(self, request, view):
        return get_authenticated_user_rank(request.user) >= ROLE_RANKING['Project Manager']


class IsSupervisorOrHigher(BasePermission):
    """Allows access to Supervisors and Admins."""
    def has_permission(self, request, view):
        return get_authenticated_user_rank(request.user) >= ROLE_RANKING['Supervisor']


class IsAdminUserTier(BasePermission):
    """Strictly locks endpoint access to Admin users only."""
    def has_permission(self, request, view):
        return get_authenticated_user_rank(request.user) >= ROLE_RANKING['Admin']