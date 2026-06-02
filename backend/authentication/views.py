from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction

from authentication.models import Role, User
from authentication.serializers import RoleSerializer, UserSerializer

class IsSupervisorOrAdmin(permissions.BasePermission):
    """
    RBAC Authorization Gateway.
    Permits read diagnostics, but blocks modification paths 
    unless the identity context resolves to a Supervisor or Administrator node.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
            
        return request.user.role.name in ['Supervisor', 'Admin'] or request.user.is_superuser


class UserProfileView(APIView):
    """
    Zero-Trust Profile Resolution Layer. Explicitly bound to JWT token authentication.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    @action(detail=True, methods=['get'], url_path='subordinates-tree')
    def subordinates_tree(self, request, pk=None):
        """
        Recursively traverses down through all nested organizational layers.
        """
        root_role = self.get_object()
        
        def build_tree(role_node):
            subordinates = role_node.subordinates.all()
            return {
                "id": role_node.id,
                "name": role_node.name,
                "subordinates": [build_tree(sub) for sub in subordinates]
            }
            
        tree_data = build_tree(root_role)
        return Response(tree_data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    # OPTIMIZATION: Prefetch roles to minimize database queries (N+1 query problem prevention)
    queryset = User.objects.all().select_related('role')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Intercepts creation to ensure only Admin profiles can assign roles to new users.
        """
        if 'role' in request.data and request.data['role'] is not None:
            if not self._is_system_admin(request.user):
                raise ValidationError({"role": "Privilege Escalation Blocked: Only System Administrators can assign user roles."})
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Protects existing user records from unauthorized role modification.
        """
        instance = self.get_object()
        
        if 'role' in request.data:
            new_role_id = request.data.get('role')
            current_role_id = instance.role.id if instance.role else None
            
            # If the role integer ID is altered, assert administrative authorization clearing
            if new_role_id is not None and int(new_role_id) != current_role_id:
                if not self._is_system_admin(request.user):
                    raise ValidationError({"role": "Privilege Escalation Blocked: Only System Administrators can alter user roles."})
                    
        return super().update(request, *args, **kwargs)

    def _is_system_admin(self, user):
        """
        Evaluates the authorization level of the user context.
        """
        return user.is_superuser or (hasattr(user, 'role') and user.role and user.role.name == 'Admin')