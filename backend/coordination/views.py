# backend/coordination/views.py
from rest_framework import viewsets, status, views, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import Workspace, WorkspaceMembership, Project, ProjectMembership, Role, Task, TaskDependency
from .serializers import ProjectSerializer, TaskSerializer, TaskDependencySerializer

class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    Manages Workspace infrastructure context boundaries.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False):
            return Workspace.objects.all()
        return Workspace.objects.filter(memberships__user=user).distinct()

    def perform_create(self, serializer):
        with transaction.atomic():
            workspace = serializer.save(created_by=self.request.user)
            WorkspaceMembership.objects.create(
                user=self.request.user,
                workspace=workspace,
                is_admin=True
            )


class ProjectViewSet(viewsets.ModelViewSet):
    """
    Manages high-level research project boundaries. 
    Enforces absolute tenant isolation by reading context from membership rosters.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False):
            return Project.objects.all().prefetch_related('tasks__assigned_to')
            
        return Project.objects.filter(
            memberships__user=user
        ).prefetch_related('tasks__assigned_to').distinct()

    def perform_create(self, serializer):
        with transaction.atomic():
            project = serializer.save(created_by=self.request.user)
            
            # Repaired explicit local model destination target pathing
            admin_role, _ = Role.objects.get_or_create(name="PROJECT_ADMIN")
            ProjectMembership.objects.create(
                user=self.request.user,
                project=project,
                role=admin_role
            )


class TaskViewSet(viewsets.ModelViewSet):
    """
    Exposes mutation interfaces for Kanban operations and Gantt tracking workflows.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(
            project__memberships__user=user
        ).select_related('assigned_to').prefetch_related('dependencies__depends_on')

        project_id = self.request.query_params.get('project', None)
        if project_id is not None:
            queryset = queryset.filter(project_id=project_id)
        return queryset.distinct()

    @action(detail=False, methods=['post'], url_path='reorder')
    @transaction.atomic
    def reorder_tasks(self, request):
        """
        API Endpoint that updates the column states and positions of multiple tasks 
        simultaneously after a drag-and-drop operation.
        """
        ordered_ids = request.data.get('ordered_ids', [])
        target_column_id = request.data.get('column_id') # Changed property binding mapping directly to Column model keys

        if not ordered_ids or not target_column_id:
            raise ValidationError({"detail": "ordered_ids and column_id fields are required."})

        locked_tasks = Task.objects.select_for_update().filter(
            id__in=ordered_ids,
            project__memberships__user=request.user
        )
        
        task_map = {str(task.id): task for task in locked_tasks}
        
        if len(task_map) != len(ordered_ids):
            raise PermissionDenied({"detail": "Access Denied: One or more target elements are unauthorized or missing."})

        updated_batch = []
        for index, task_id in enumerate(ordered_ids):
            task_instance = task_map[str(task_id)]
            task_instance.column_id = target_column_id
            task_instance.position = index # Synchronized field parameter targets cleanly
            updated_batch.append(task_instance)

        Task.objects.bulk_update(updated_batch, ['column_id', 'position'])
        return Response({"status": "Batch reordering synchronization complete."}, status=status.HTTP_200_OK)


class TaskDependencyViewSet(viewsets.ModelViewSet):
    """
    Maps Directed Acyclic Graph pathways for scheduling constraints.
    """
    serializer_class = TaskDependencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TaskDependency.objects.filter(
            task__project__memberships__user=user
        ).distinct()