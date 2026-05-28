from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Project, Task, TaskDependency
from .serializers import ProjectSerializer, TaskSerializer, TaskDependencySerializer

# FIXED: Removed the invalid viewsets.ModelSerializer inheritance parameter
class ProjectViewSet(viewsets.ModelViewSet):
    """
    Manages high-level research project boundaries.
    """
    queryset = Project.objects.all().prefetch_related('tasks__assigned_to')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically bind the creating user to enforce data lineage trace rules
        serializer.save(created_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    Exposes mutation interfaces for Kanban operations and Gantt tracking workflows.
    """
    queryset = Task.objects.all().select_related('assigned_to').prefetch_related('dependencies__depends_on')
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filters tracking elements by their parent scope coordinates when supplied.
        """
        queryset = self.queryset
        project_id = self.request.query_params.get('project', None)
        if project_id is not None:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @action(detail=False, methods=['post'], url_path='reorder')
    @transaction.atomic
    def reorder_tasks(self, request):
        """
        API Endpoint that updates the column states and positions of multiple tasks 
        simultaneously after a drag-and-drop operation.
        Expects payload: {"ordered_ids": [uuid, uuid, uuid], "status": "IN_PROGRESS"}
        """
        ordered_ids = request.data.get('ordered_ids', [])
        target_status = request.data.get('status')

        if not ordered_ids or not target_status:
            return Response(
                {"error": "Missing execution mapping requirements: ordered_ids and status fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Shift processing indices matching array sequence positioning parameters
            for index, task_id in enumerate(ordered_ids):
                Task.objects.filter(id=task_id).update(
                    status=target_status,
                    column_order=index
                )
            return Response({"status": "Batch reordering synchronization complete."}, status=status.HTTP_200_OK)
        except Exception as error_context:
            return Response({"error": str(error_context)}, status=status.HTTP_400_BAD_REQUEST)


class TaskDependencyViewSet(viewsets.ModelViewSet):
    """
    Maps Directed Acyclic Graph pathways for scheduling constraints.
    """
    queryset = TaskDependency.objects.all()
    serializer_class = TaskDependencySerializer
    permission_classes = [IsAuthenticated]