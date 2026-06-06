# backend/kanban/serializers.py

from rest_framework import serializers
from .models import Board, Column, Task
from authentication.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'column', 'title', 'description', 'position', 
            'priority', 'assigned_to', 'assigned_to_details', 
            'created_by', 'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ColumnSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ['id', 'board', 'name', 'position', 'tasks']


class BoardSerializer(serializers.ModelSerializer):
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'columns', 'created_at']