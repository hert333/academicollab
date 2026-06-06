from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
from .permissions import HierarchicalRolePermission

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('tasks')
    serializer_class = ProjectSerializer
    permission_classes = [HierarchicalRolePermission]
    model_name = 'project'

    def perform_create(self, serializer):
        # Enforce tracking context continuity by binding the creator directly
        serializer.save(created_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [HierarchicalRolePermission]
    model_name = 'task'

    @action(detail=False, methods=['post'], url_path='reorder-kanban')
    def reorder_kanban(self, request):
        """
        Concurrency Protection Vector: Leverages transaction isolation loops
        to alter structural index listings while preventing double-submit mutations.
        """
        task_orders = request.data.get('task_orders', []) # Expected format: [{"id": 1, "order": 0, "status": "TODO"}, ...]
        
        if not task_orders:
            return Response({"error": "No processing payload submitted."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Enforce an absolute lock across calculations to safeguard indexing stability
            with transaction.atomic():
                task_ids = [item['id'] for item in task_orders]
                # select_for_update blocks concurrent transactions from touching row indexes until this frame releases
                tasks = Task.objects.select_for_update().filter(id__in=task_ids)
                task_map = {task.id: task for task in tasks}

                for item in task_orders:
                    task_obj = task_map.get(int(item['id']))
                    if task_obj:
                        task_obj.order = item['order']
                        task_obj.status = item['status']
                        task_obj.save()

            return Response({"status": "Kanban indexing sequence altered successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"State synchronization failure: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)