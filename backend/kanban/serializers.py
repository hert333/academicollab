# backend/kanban/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from coordination.models import Project
from .models import KanbanColumn, Task

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserMinimalSerializer(source='assigned_to', read_only=True)
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Task.objects.all(), 
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'column', 'assigned_to', 'assigned_to_detail', 'title', 
            'description', 'order', 'priority', 'due_date', 'start_date', 
            'end_date', 'dependencies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order', 'created_at', 'updated_at']

    def validate(self, attrs):
        instance = self.instance
        start_date = attrs.get('start_date', instance.start_date if instance else None)
        end_date = attrs.get('end_date', instance.end_date if instance else None)
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "start_date": "Task timeline configuration anomaly: start_date cannot occur subsequent to end_date."
            })
        return attrs


class KanbanColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    name = serializers.CharField(required=False, max_length=100)
    title = serializers.CharField(required=False, max_length=100)
    
    # Allow order to be explicitly evaluated during deserialization validation
    order = serializers.IntegerField(required=False)

    class Meta:
        model = KanbanColumn
        fields = ['id', 'project', 'name', 'title', 'order', 'tasks']
        # Empty this array so order can be calculated or accepted from payloads
        read_only_fields = []

    def validate(self, attrs):
        """
        Normalizes payload properties and prevents sequence collisions.
        """
        # 1. Resolve naming strategy variations between frontend and backend contracts
        resolved_name = attrs.get('name') or attrs.pop('title', None)
        if not resolved_name:
            raise serializers.ValidationError({
                "name": "Column naming vector missing: Either 'name' or 'title' field attributes must be provided."
            })
        attrs['name'] = resolved_name

        # 2. Dynamic Auto-Increment Logic for Sequence Ordering
        # If no explicit order is provided, find the next available slot for this specific project
        project = attrs.get('project')
        if project and 'order' not in attrs:
            # Counts existing columns to generate a clean, zero-indexed incremental integer
            attrs['order'] = project.kanban_columns.count()

        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    columns = KanbanColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'columns']