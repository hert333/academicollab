from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Project, Task, TaskDependency

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Provides lightweight identity maps for task assignments without exposing 
    sensitive credential hashes or system flags.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


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
        # Form an ephemeral model instance to invoke model-level validation logic
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
            'id', 'project', 'title', 'description', 'status', 
            'column_order', 'start_date', 'due_date', 
            'assigned_to', 'assigned_to_detail', 'dependencies', 
            'blocked_tasks', 'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        """
        Validates temporal parameters before committing database write sequences.
        """
        start_date = attrs.get('start_date', self.instance.start_date if self.instance else None)
        due_date = attrs.get('due_date', self.instance.due_date if self.instance else None)
        
        if start_date and due_date and start_date > due_date:
            raise serializers.ValidationError({
                "start_date": "Temporal Anomaly: Task start scheduling window cannot close before it opens."
            })
        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'created_by', 'created_by_detail', 'tasks', 'created_at', 'updated_at']
        read_only_fields = ['created_by']