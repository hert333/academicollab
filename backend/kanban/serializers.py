from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, KanbanColumn, Task

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserMinimalSerializer(source='assigned_to', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'column', 'assigned_to', 'assigned_to_detail', 'title', 'description', 'order', 'priority', 'due_date', 'created_at', 'updated_at']
        read_only_fields = ['order']

class KanbanColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = KanbanColumn
        fields = ['id', 'project', 'name', 'order', 'tasks']
        read_only_fields = ['order']

class ProjectSerializer(serializers.ModelSerializer):
    columns = KanbanColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'columns']