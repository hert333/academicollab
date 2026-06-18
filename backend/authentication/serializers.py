# backend/authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password
from authentication.models import Role, User
from authentication.permissions import is_system_admin


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer to map system permission nodes for structural validation check steps.
    """
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer mapping the hierarchical multi-tenant Role graph data engine.
    """
    inherited_permissions = serializers.SerializerMethodField()
    subordinates_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 
            'name', 
            'parent', 
            'permissions', 
            'inherited_permissions', 
            'subordinates_count'
        ]

    def get_inherited_permissions(self, obj):
        # Fetches inherited database permissions assigned up the hierarchy tree
        permissions = obj.get_all_permissions()
        return PermissionSerializer(permissions, many=True).data

    def get_subordinates_count(self, obj):
        return obj.subordinates.count()

    def validate(self, attrs):
        """
        Structural Integrity Engine: Prevents cycle creation inside the role tree.
        Absolute administrators bypass this layout to perform foundational adjustments.
        """
        request = self.context.get('request')
        user = request.user if request else None

        # Absolute Admin Bypass Guard Clause for Structural Metrics Mutations
        if user and is_system_admin(user):
            return attrs

        parent = attrs.get('parent', self.instance.parent if self.instance else None)
        
        if self.instance and parent:
            if parent.id == self.instance.id:
                raise serializers.ValidationError({
                    "parent": "Structural Error: A role node cannot be designated as its own parent."
                })
            
            ancestor_ids = parent.get_ancestor_ids()
            if self.instance.id in ancestor_ids:
                raise serializers.ValidationError({
                    "parent": "Structural Error: Circular dependency detected within the requested role tree branch."
                })

        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Optimized User Model Serializer with advanced password lifecycle protection
    and Zero-Trust field-level access control boundaries.
    """
    role_details = RoleSerializer(source='role', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'password', 
            'role', 
            'role_details', 
            'is_active'
        ]
        extra_kwargs = {
            'password': {
                'write_only': True,
                'required': False,
                'style': {'input_type': 'password'}
            }
        }

    def validate_role(self, value):
        """
        Zero-Trust Integrity Bound: Validates that the requesting user cannot 
        assign a role that matches or exceeds their own clearance level.
        """
        request = self.context.get('request')
        if not request or not request.user:
            return value

        # System administrative tokens bypass the hierarchical validation pipeline completely
        if is_system_admin(request.user):
            return value

        current_user_role = request.user.role
        if not current_user_role:
            raise serializers.ValidationError("Identity mapping missing: Your account has no assigned role.")

        if value:
            # Prevent users from modifying profiles to assign a role higher or equal to their own rank.
            actor_role_id = current_user_role.id
            target_role_ancestors = value.get_ancestor_ids()

            if actor_role_id not in target_role_ancestors or actor_role_id == value.id:
                raise serializers.ValidationError(
                    "Access Denied: Cannot assign a role matching or exceeding your tree clearance level."
                )

        return value

    def create(self, validated_data):
        if 'password' in validated_data:
            validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)