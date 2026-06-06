from rest_framework import serializers
from .models import Project, Task

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'title', 'description', 'status', 
            'order', 'start_date', 'end_date', 'depends_on', 
            'assigned_to', 'assigned_to_username'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """
        Gantt State Constraint Rule: Ensures temporal continuity boundaries 
        are preserved before database engine commit.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "Temporal Integrity Error: End date cannot precede the execution start date."
            })
        return data


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username', 'created_at', 'tasks']
        read_only_fields = ['id', 'created_by', 'created_at']