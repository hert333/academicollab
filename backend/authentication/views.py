from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction

from authentication.models import Role, User
from authentication.serializers import RoleSerializer, UserSerializer

# Absolute hierarchical authority map used for RBAC calculations
ROLE_RANKING = {
    'Student': 1,
    'Project Manager': 2,
    'Supervisor': 3,
    'Admin': 4,
}

def get_identity_rank(user) -> int:
    """
    Safely resolves the numeric permission rank of the user context.
    Ensures strict fallback behaviors for unassigned profiles.
    """
    if not user or not user.is_authenticated:
        return 0
    if user.is_superuser:
        return ROLE_RANKING['Admin']
    if hasattr(user, 'role') and user.role:
        return ROLE_RANKING.get(user.role.name, ROLE_RANKING['Student'])
    return ROLE_RANKING['Student']


class IsSupervisorOrAdmin(permissions.BasePermission):
    """
    Hierarchical RBAC Authorization Engine.
    Permits read diagnostics across endpoints, but blocks modification paths 
    unless the identity context meets or exceeds the Supervisor tier.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return get_identity_rank(request.user) >= ROLE_RANKING['Supervisor']


class IsProjectManagerOrHigher(permissions.BasePermission):
    """
    Granular Access Guard for workflow coordination layouts.
    Blocks access for baseline Student tokens.
    """
    def has_permission(self, request, view):
        return get_identity_rank(request.user) >= ROLE_RANKING['Project Manager']


class UserProfileView(APIView):
    """
    Zero-Trust Profile Resolution Layer explicitly bound to verified JWT contexts.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    """
    Administrative Role Definition Controller.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    @action(detail=True, methods=['get'], url_path='subordinates-tree')
    def subordinates_tree(self, request, pk=None):
        """
        Recursively traverses organizational node paths.
        """
        root_role = self.get_object()
        
        def build_tree(role_node):
            subordinates = role_node.subordinates.all()
            return {
                "id": role_node.id,
                "name": role_node.name,
                "subordinates": [build_tree(sub) for sub in subordinates]
            }
            
        return Response(build_tree(root_role), status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    Identity Management Controller with transactional role mutation safeguards.
    """
    queryset = User.objects.all().select_related('role')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    def _assert_mutation_authority(self, request, current_instance=None):
        """
        Enforces strict separation of duties.
        Blocks non-Admin users from making explicit role assignment changes.
        """
        # Scan incoming payload for role adjustments
        if 'role' in request.data:
            new_role_val = request.data.get('role')
            
            # Determine if operation modifies an existing role state
            if current_instance:
                current_role_id = current_instance.role.id if current_instance.role else None
                try:
                    is_changed = (new_role_val is not None and int(new_role_val) != current_role_id) or \
                                 (new_role_val is None and current_role_id is not None)
                except (ValueError, TypeError):
                    is_changed = True
            else:
                # For creation paths, check if any non-null role is being assigned
                is_changed = new_role_val is not None

            if is_changed and get_identity_rank(request.user) < ROLE_RANKING['Admin']:
                raise ValidationError({
                    "role": "Privilege Escalation Blocked: Only System Administrators hold authorization to assign or modify user role values."
                })

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Intercepts user creation requests to block unauthorized role assignments.
        """
        self._assert_mutation_authority(request, current_instance=None)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Intercepts standard PUT requests to block unauthorized role adjustments.
        """
        instance = self.get_object()
        self._assert_mutation_authority(request, current_instance=instance)
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """
        Intercepts PATCH requests to close the partial update security vulnerability.
        """
        instance = self.get_object()
        self._assert_mutation_authority(request, current_instance=instance)
        return super().partial_update(request, *args, **kwargs)