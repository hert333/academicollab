# backend/workspace/views.py
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Workspace, Project, Task  # Included Workspace model
from .serializers import WorkspaceSerializer, ProjectSerializer, TaskSerializer
from .permissions import WorkspaceHierarchicalRBACPermission

class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    API ViewSet managing top-level Academic Isolation Workspaces.
    """
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Zero-Trust Evaluation: Platform ADMINs read all infrastructure segments.
        Standard users see only the partitions they explicitly created or are assigned to.
        """
        user = self.request.user
        
        # Safely extract the role name string handling both dictionary configurations and related model objects
        role_name = ""
        if hasattr(user, 'role_details') and isinstance(user.role_details, dict):
            role_name = user.role_details.get('name', '')
        elif hasattr(user, 'role') and user.role:
            # If user.role is a related model instance, safely extract its name attribute or convert to string
            role_name = getattr(user.role, 'name', str(user.role))
            
        current_role = str(role_name).upper()
        
        if current_role == 'ADMIN':
            return Workspace.objects.all().order_by('-created_at')
            
        return Workspace.objects.filter(
            Q(created_by=user) | Q(projects__memberships__user=user)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        """ Bind the provisioning operator to the created_by tracking field """
        serializer.save(created_by=self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API ViewSet managing multi-tenant Project workspaces.
    Enforces absolute role isolation via explicit runtime queries.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, WorkspaceHierarchicalRBACPermission]

    def get_queryset(self):
        """
        Zero Trust Backend Strategy: Limits visibility strictly to workspaces where 
        the operator is the creator or has a valid project membership record.
        """
        return Project.objects.filter(
            Q(created_by=self.request.user) | 
            Q(memberships__user=self.request.user)
        ).distinct().prefetch_related('tasks').order_by('-created_at')

    def perform_create(self, serializer):
        """ Enforce tracking context continuity by binding the creator directly """
        serializer.save(created_by=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    API ViewSet managing individual Task workflows, Kanban column positions, 
    and Gantt timeline dependency linkages.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, WorkspaceHierarchicalRBACPermission]

    def get_queryset(self):
        """
        Limits active task queries to parent projects where the authenticated 
        operator holds an active workspace registration profile.
        """
        return Task.objects.filter(
            project__memberships__user=self.request.user
        ).select_related('project', 'assigned_to', 'depends_on').distinct()

    @action(detail=False, methods=['post'], url_path='reorder-kanban')
    def reorder_kanban(self, request):
        """
        Concurrency & Tenancy Protection Vector: Bulk alters Kanban indices 
        while strictly locking resources and validating tenant boundaries.
        """
        task_orders = request.data.get('task_orders', [])
        
        if not task_orders:
            return Response({"error": "No processing payload submitted."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            task_ids = [int(item['id']) for item in task_orders]
        except (ValueError, TypeError):
            return Response({"error": "Malformed payload structure: IDs must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce an absolute lock across calculations to safeguard indexing stability
        with transaction.atomic():
            # Zero-Trust Verification: Select and lock rows, but only if they belong to the user's workspaces
            tasks = Task.objects.select_for_update().filter(
                id__in=task_ids,
                project__memberships__user=request.user
            )
            task_map = {task.id: task for task in tasks}

            # If any requested task is missing from the scoped queryset, reject the batch operation
            if len(task_map) != len(set(task_ids)):
                raise PermissionDenied("Unauthorized operation: Multi-tenant boundary violation detected.")

            # Apply batch operations safely under row-level database locks
            for item in task_orders:
                task_obj = task_map.get(int(item['id']))
                if task_obj:
                    # Enforce that Members can only reorder tasks assigned to them
                    # While Leads or Supervisors can manage layout rules globally
                    from workspace.permissions import get_user_project_role
                    role = get_user_project_role(request.user, task_obj.project)
                    
                    if role not in ['SUPERVISOR', 'LEAD'] and task_obj.assigned_to != request.user:
                        raise PermissionDenied(f"You lack privileges to move Task #{task_obj.id}.")

                    task_obj.order = item['order']
                    task_obj.status = item['status']
                    task_obj.save(update_fields=['order', 'status'])

            return Response({"status": "Kanban indexing sequence altered successfully."}, status=status.HTTP_200_OK)