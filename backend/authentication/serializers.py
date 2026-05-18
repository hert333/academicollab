from rest_framework import serializers
from authentication.models import Role, User
from django.contrib.auth.models import Permission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class RoleSerializer(serializers.ModelSerializer):
    # Retrieve flat lists of all inherited permission objects up the tree hierarchy
    inherited_permissions = serializers.SerializerMethodField()
    subordinates_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'parent', 'permissions', 'inherited_permissions', 'subordinates_count']

    def get_inherited_permissions(self, obj):
        permissions = obj.get_all_permissions()
        return PermissionSerializer(permissions, many=True).data

    def get_subordinates_count(self, obj):
        return obj.subordinates.count()

class UserSerializer(serializers.ModelSerializer):
    role_details = RoleSerializer(source='role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_details', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}
