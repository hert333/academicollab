from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from authentication.models import Role, User
from authentication.serializers import RoleSerializer, UserSerializer

class IsSupervisorOrAdmin(permissions.BasePermission):
    """
    RBAC Authorization Gateway.
    Permits unhindered read diagnostics, but blocks model mutation paths 
    unless the identity context resolves to a Supervisor or Administrator node.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Guard against unauthenticated anomalies or empty profile bindings
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False
            
        return request.user.role.name in ['Supervisor', 'Admin'] or request.user.is_superuser


class UserProfileView(APIView):
    """
    Zero-Trust Profile Resolution Layer. Explicitly bound to JWT token authentication
    to prevent configuration drift or fallback to basic session cookies.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        # FIXED: Resolved AttributeError by migrating from HTTP_OK to HTTP_200_OK
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    # FIXED: Hardened write paths using strict hierarchical RBAC checking
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]

    @action(detail=True, methods=['get'], url_path='subordinates-tree')
    def subordinates_tree(self, request, pk=None):
        """
        Recursively traverses down through all nested organizational layers 
        to output the full down-tree hierarchy required for HCI interface components.
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # FIXED: Restricts student accounts from creating, updating, or deleting platform identities
    permission_classes = [IsAuthenticated, IsSupervisorOrAdmin]