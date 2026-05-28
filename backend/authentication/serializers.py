from rest_framework import serializers
from authentication.models import Role, User
from django.contrib.auth.models import Permission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class RoleSerializer(serializers.ModelSerializer):
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
        # FIXED: Added explicit 'password' field mapping to the context fields list
        fields = ['id', 'username', 'email', 'password', 'role', 'role_details', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}}
        }

    def create(self, validated_data):
        # FIXED: Strips out plain strings and invokes Django's secure hashing abstraction layer
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        # FIXED: Protects existing instances from plaintext password overrides during modifications
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user