# backend/kanban/serializers.py
from rest_framework import serializers
from .models import KanbanColumn
from coordination.models import Task

class TaskSerializer(serializers.ModelSerializer):
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=Task.objects.none(),
        required=False
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'column', 
            'assigned_to', 'dependencies', 'column_order', 
            'created_at', 'updated_at'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['dependencies'].queryset = Task.objects.filter(
                column__project__memberships__user=request.user
            ).distinct()


class KanbanColumnSerializer(serializers.ModelSerializer):
    # FIXED: Eliminated redundant source='tasks' configuration declaration
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = KanbanColumn
        fields = ['id', 'project', 'name', 'order', 'tasks']