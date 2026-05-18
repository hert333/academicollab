from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from authentication.models import Role, User
from authentication.serializers import RoleSerializer, UserSerializer

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    @action(detail=True, methods=['get'])
    def clear_hierarchy(self, request, pk=None):
        """
        Custom endpoint to fetch the specific role and all branches below it.
        Path: /api/roles/{id}/clear_hierarchy/
        """
        role = self.get_object()
        subordinates = role.subordinates.all()
        serializer = self.get_serializer(subordinates, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
