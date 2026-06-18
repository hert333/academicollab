# backend/coordination/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Workspace, Project, Task, TaskDependency

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Provides lightweight identity maps for task assignments without exposing 
    sensitive credential hashes or system flags.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializes top-tier organization workspace blocks.
    """
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'created_by', 'created_by_detail', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_by_detail', 'created_at', 'updated_at']


class TaskDependencySerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    depends_on_title = serializers.CharField(source='depends_on.title', read_only=True)

    class Meta:
        model = TaskDependency
        fields = ['id', 'task', 'task_title', 'depends_on', 'depends_on_title']

    def validate(self, attrs):
        """
        Executes structural integrity checks against the instantiating model constraints.
        """
        instance = TaskDependency(**attrs)
        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserMinimalSerializer(source='assigned_to', read_only=True)
    dependencies = TaskDependencySerializer(many=True, read_only=True)
    blocked_tasks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'column', 'title', 'description', 
            'priority', 'position', 'start_date', 'end_date', 
            'assigned_to', 'assigned_to_detail', 'dependencies', 
            'blocked_tasks', 'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        """
        Merges partial update fields securely into a transient validation model instance 
        to trigger clean data cleaning blocks across both POST and PATCH routes.
        """
        if self.instance:
            instance = self.instance
            for attribute, value in attrs.items():
                setattr(instance, attribute, value)
        else:
            instance = Task(**attrs)

        try:
            instance.full_clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    workspace = serializers.PrimaryKeyRelatedField(
        queryset=Workspace.objects.all(), 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = Project
        fields = [
            'id', 'workspace', 'title', 'description', 'created_by', 
            'created_by_detail', 'tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by']