from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import F
from .models import Project, KanbanColumn, Task
from .serializers import ProjectSerializer, KanbanColumnSerializer, TaskSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('columns__tasks')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

class KanbanColumnViewSet(viewsets.ModelViewSet):
    queryset = KanbanColumn.objects.all()
    serializer_class = KanbanColumnSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='reorder-columns')
    def reorder_columns(self, request, pk=None):
        """
        Handles horizontal column shifting logic within a single project context.
        Expects payload format: { "new_order": integer }
        """
        column = self.get_object()
        new_order = int(request.data.get('new_order'))
        project_id = column.project_id

        with transaction.atomic():
            columns = KanbanColumn.objects.select_for_update().filter(project_id=project_id)
            old_order = column.order

            if old_order < new_order:
                columns.filter(order__gt=old_order, order__lte=new_order).update(order=F('order') - 1)
            elif old_order > new_order:
                columns.filter(order__gte=new_order, order__lt=old_order).update(order=F('order') + 1)

            column.order = new_order
            column.save()

        return Response({'status': 'Column alignment reordered successfully'}, status=status.HTTP_200_OK)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        column = serializer.validated_data['column']
        # Set task index at the bottom of the column target tree
        task_count = Task.objects.filter(column=column).count()
        serializer.save(order=task_count)

    @action(detail=True, methods=['post'], url_path='reorder')
    def reorder_task(self, request, pk=None):
        """
        Executes structural drag-and-drop positional mathematics across or within task columns.
        Expects payload format: { "target_column_id": "UUID", "new_order": integer }
        """
        task = self.get_object()
        target_column_id = request.data.get('target_column_id')
        new_order = int(request.data.get('new_order'))

        if not target_column_id:
            return Response({'error': 'Missing target_column_id attribute'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            old_column = task.column
            old_order = task.order
            
            # Row lock targets to block concurrent mutators from generating duplicate sequence offsets
            target_column = KanbanColumn.objects.get(pk=target_column_id)

            if old_column == target_column:
                # Intracolumn mutation math
                tasks = Task.objects.select_for_update().filter(column=target_column)
                if old_order < new_order:
                    tasks.filter(order__gt=old_order, order__lte=new_order).update(order=F('order') - 1)
                elif old_order > new_order:
                    tasks.filter(order__gte=new_order, order__lt=old_order).update(order=F('order') + 1)
            else:
                # Intercolumn structural shifting math
                Task.objects.select_for_update().filter(column=old_column, order__gt=old_order).update(order=F('order') - 1)
                Task.objects.select_for_update().filter(column=target_column, order__gte=new_order).update(order=F('order') + 1)

            task.column = target_column
            task.order = new_order
            task.save()

        return Response({'status': 'Task positional mapping adjusted'}, status=status.HTTP_200_OK)