# backend/authentication/views.py
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import transaction
from collections import defaultdict

from authentication.models import Role, User
from authentication.serializers import RoleSerializer, UserSerializer
from authentication.permissions import IsMinimumHierarchicalRole

# Cross-App imports cleanly decoupled to handle allocations
from coordination.models import ProjectMembership, Project as CoordinationProject


def verify_hierarchical_clearance(user, minimum_allowed_role: str) -> bool:
    """
    Validates user clearance levels outside standard ViewSet routing pipelines.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not user.role:
        return False

    # Short-Circuit: Administrative matching criteria
    if user.role.name.upper() in ['ADMIN', 'SYSTEM ADMINISTRATOR']:
        return True

    if user.role.name.upper() == minimum_allowed_role.upper():
        return True

    try:
        target_base_role = Role.objects.get(name__iexact=minimum_allowed_role)
        allowed_role_ids = target_base_role.get_ancestor_ids()
        return user.role.id in allowed_role_ids
    except Role.DoesNotExist:
        return False


class UserProfileView(APIView):
    """
    Zero-Trust Profile Resolution Layer explicitly bound to verified JWT contexts.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    """
    Administrative Role Definition Controller.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMinimumHierarchicalRole]
    required_minimum_role = 'SUPERVISOR'

    @action(detail=True, methods=['get'], url_path='subordinates-tree')
    def subordinates_tree(self, request, pk=None):
        """
        Builds the organizational tree entirely in-memory using an adjacency map.
        """
        root_role = self.get_object()
        all_roles = list(Role.objects.all())
        
        adjacency_map = defaultdict(list)
        for role in all_roles:
            if role.parent_id:
                adjacency_map[role.parent_id].append(role)
        
        def build_tree(role_node):
            subordinates = adjacency_map[role_node.id]
            return {
                "id": role_node.id,
                "name": role_node.name,
                "subordinates": [build_tree(sub) for sub in subordinates]
            }
            
        return Response(build_tree(root_role), status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """
    Identity Management Controller with transactional role mutation safeguards
    and atomic multi-tenant user provisioning capabilities.
    """
    queryset = User.objects.all().select_related('role')
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsMinimumHierarchicalRole]
    required_minimum_role = 'SUPERVISOR'

    def _assert_mutation_authority(self, request, current_instance=None):
        """
        Enforces separation of duties.
        Blocks non-ADMIN profiles from altering account roles.
        """
        if 'role' in request.data:
            new_role_val = request.data.get('role')
            
            if current_instance:
                current_role_id = current_instance.role.id if current_instance.role else None
                try:
                    is_changed = (new_role_val is not None and int(new_role_val) != current_role_id) or \
                                 (new_role_val is None and current_role_id is not None)
                except (ValueError, TypeError):
                    is_changed = True
            else:
                is_changed = new_role_val is not None

            if is_changed:
                user = request.user
                is_admin = (
                    user.is_superuser or 
                    (hasattr(user, 'role') and user.role and user.role.name.upper() in ['ADMIN', 'SYSTEM ADMINISTRATOR']) or
                    verify_hierarchical_clearance(user, 'ADMIN')
                )
                
                if not is_admin:
                    raise ValidationError({
                        "role": "Privilege Escalation Blocked: Only System Administrators hold authorization to assign or modify user role values."
                    })

    def _is_request_user_admin(self, user):
        """Helper to evaluate absolute admin clearance."""
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or (user.role and user.role.name.upper() in ['ADMIN', 'SYSTEM ADMINISTRATOR'])

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._assert_mutation_authority(request, current_instance=None)
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._assert_mutation_authority(request, current_instance=instance)
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._assert_mutation_authority(request, current_instance=instance)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='provision')
    @transaction.atomic
    def provision(self, request):
        """
        Atomic Provisioning Endpoint: Creates a system account and binds them to a 
        project space workspace inside a single transaction isolation block.
        Expected Payload: { "username": "...", "email": "...", "password": "...", "role": id, "project_id": "UUID" }
        """
        # 1. Access Control Boundary Lock
        if not self._is_request_user_admin(request.user):
            raise PermissionDenied("Access Denied: Only platform administrators hold authorization to provision accounts.")

        project_id = request.data.get('project_id')
        role_id = request.data.get('role')  # Mapped to match user serializer context

        if not project_id:
            raise ValidationError({"project_id": "This field is required to allocate users to a workspace."})

        # 2. Invoke Serializer Execution Loop (Creates the base user and encrypts password)
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 3. Handle Cross-App Relational Mappings Atomically
        try:
            target_project = CoordinationProject.objects.get(id=project_id)
            target_role = Role.objects.get(id=role_id) if role_id else user.role

            if not target_role:
                raise ValidationError("The specified user must have a valid security role layer attached.")

            # Build the physical multi-tenant access registration matrix link
            ProjectMembership.objects.create(
                user=user,
                project=target_project,
                role=target_role
            )

        except CoordinationProject.DoesNotExist:
            raise ValidationError({"project_id": f"Target workspace project context '{project_id}' does not exist."})
        except Role.DoesNotExist:
            raise ValidationError({"role": f"Target role context assignment layer '{role_id}' does not exist."})

        # Return fully verified profile dataset
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)