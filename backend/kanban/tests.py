# backend/kanban/views.py
from django.db import transaction
from django.db.models import F
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import KanbanColumn
from coordination.models import Task, Project, ProjectMembership
from .serializers import KanbanColumnSerializer, TaskSerializer

def get_user_project_role(user, project):
    """
    Direct multi-tenant lookup validating the user's operational scope 
    bypassing localized queryset filtering limitations.
    """
    if not user or user.is_anonymous or not project:
        return None
    membership = ProjectMembership._base_manager.filter(user=user, project=project).select_related('role').first()
    if membership and membership.role:
        return membership.role.name.upper()
    return None


class KanbanColumnViewSet(viewsets.ModelViewSet):
    serializer_class = KanbanColumnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Scopes standard collection listings strictly to verified members. """
        return KanbanColumn.objects.filter(project__memberships__user=self.request.user).order_by('order')

    def initial(self, request, *args, **kwargs):
        """
        Intercepts execution at the entry point to catch cross-tenant multi-tenant 
        access attempts before they leak as 404 responses.
        """
        super().initial(request, *args, **kwargs)
        
        action_name = self.action
        if not action_name and hasattr(request, 'method'):
            method_map = {'GET': 'retrieve' if self.kwargs else 'list', 'PUT': 'update', 'PATCH': 'partial_update', 'DELETE': 'destroy', 'POST': 'create'}
            action_name = method_map.get(request.method.upper(), '')

        # Create Validation
        if action_name == 'create':
            project_id = request.data.get('project')
            if project_id:
                project = Project._base_manager.filter(id=project_id).first()
                if not project:
                    raise Http404("Target project workspace does not exist.")
                role = get_user_project_role(request.user, project)
                if not role or role not in ['LEAD', 'SUPERVISOR']:
                    raise PermissionDenied("You do not have permission to create columns in this workspace.")

        # Detail Validation (Enforce 403 Forbidden over 404 for existing external rows)
        if action_name in ['retrieve', 'update', 'partial_update', 'destroy', 'reorder_columns']:
            lookup_value = self.kwargs.get('pk')
            if lookup_value:
                column = KanbanColumn._base_manager.filter(pk=lookup_value).select_related('project').first()
                if column:
                    role = get_user_project_role(request.user, column.project)
                    if not role:
                        raise PermissionDenied("Access to this workspace ecosystem is denied.")
                    if action_name in ['update', 'partial_update', 'destroy', 'reorder_columns']:
                        if role not in ['LEAD', 'SUPERVISOR']:
                            raise PermissionDenied("Standard members are blocked from structural layout modifications.")
                else:
                    raise Http404("Target column not found.")

    @action(detail=True, methods=['post'], url_path='reorder-columns')
    def reorder_columns(self, request, pk=None):
        column = self.get_object()
        new_order_raw = request.data.get('new_order')
        if new_order_raw is None:
            return Response({'error': 'Missing required parameter: new_order'}, status=status.HTTP_400_BAD_REQUEST)
            
        new_order = int(new_order_raw)
        with transaction.atomic():
            columns = KanbanColumn._base_manager.select_for_update().filter(project_id=column.project_id)
            if column.order < new_order:
                columns.filter(order__gt=column.order, order__lte=new_order).update(order=F('order') - 1)
            else:
                columns.filter(order__gte=new_order, order__lt=column.order).update(order=F('order') + 1)

            column.order = new_order
            column.save(update_fields=['order'])

        return Response({'status': 'Success'}, status=status.HTTP_200_OK)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """ Limits queries strictly to authorized projects to prevent multi-tenant data leaks. """
        return Task.objects.filter(column__project__memberships__user=self.request.user).select_related('assigned_to', 'column')

    def initial(self, request, *args, **kwargs):
        """
        Intercepts task lifecycle entry processing points. Evaluates structural multi-tenant 
        boundaries globally before DRF's internal queryset overrides run.
        """
        super().initial(request, *args, **kwargs)

        action_name = self.action
        if not action_name and hasattr(request, 'method'):
            method_map = {'GET': 'retrieve' if self.kwargs else 'list', 'PUT': 'update', 'PATCH': 'partial_update', 'DELETE': 'destroy', 'POST': 'create'}
            action_name = method_map.get(request.method.upper(), '')

        # Creation Security Check
        if action_name == 'create':
            column_id = request.data.get('column')
            if column_id:
                column = KanbanColumn._base_manager.filter(id=column_id).select_related('project').first()
                if not column:
                    raise Http404("Target column context does not exist.")
                role = get_user_project_role(request.user, column.project)
                if not role:
                    raise PermissionDenied("You do not have permission to add tasks to this workspace.")

        # Intercept Detail Operations to evaluate global tenancy before get_queryset excludes the row
        if action_name in ['retrieve', 'update', 'partial_update', 'destroy', 'reorder_task']:
            lookup_value = self.kwargs.get('pk')
            if lookup_value:
                task = Task._base_manager.filter(pk=lookup_value).select_related('column__project', 'assigned_to').first()
                if task:
                    role = get_user_project_role(request.user, task.column.project)
                    if not role:
                        # Exists globally but user is outside the project workspace workspace scope -> Raise 403 Forbidden
                        raise PermissionDenied("Access to this workspace ecosystem is denied.")
                    
                    # Intercept mutation actions for validation
                    if action_name in ['update', 'partial_update', 'destroy', 'reorder_task']:
                        if role not in ['LEAD', 'SUPERVISOR']:
                            if task.assigned_to != request.user:
                                raise PermissionDenied("Standard members are blocked from mutating tasks they do not own.")
                else:
                    raise Http404("Target task not found.")

    def update(self, request, *args, **kwargs):
        """ Explicitly overrides the update route handler to enforce user-level blockages. """
        task = Task._base_manager.filter(pk=kwargs.get('pk')).select_related('column__project').first()
        if not task:
            raise Http404("Target task not found.")
        
        role = get_user_project_role(request.user, task.column.project)
        if not role:
            raise PermissionDenied("Access to this workspace ecosystem is denied.")
        if role not in ['LEAD', 'SUPERVISOR'] and task.assigned_to != request.user:
            raise PermissionDenied("Standard members are blocked from mutating tasks they do not own.")
            
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """ Explicitly overrides the partial update route handler to enforce user-level blockages. """
        task = Task._base_manager.filter(pk=kwargs.get('pk')).select_related('column__project').first()
        if not task:
            raise Http404("Target task not found.")
            
        role = get_user_project_role(request.user, task.column.project)
        if not role:
            raise PermissionDenied("Access to this workspace ecosystem is denied.")
        if role not in ['LEAD', 'SUPERVISOR'] and task.assigned_to != request.user:
            raise PermissionDenied("Standard members are blocked from mutating tasks they do not own.")
            
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='reorder')
    def reorder_task(self, request, pk=None):
        task = self.get_object()
        target_column_id = request.data.get('target_column_id')
        new_order = int(request.data.get('position', 0))

        target_column = KanbanColumn._base_manager.filter(id=target_column_id).select_related('project').first()
        if not target_column:
            raise Http404("Target destination column does not exist.")
            
        target_role = get_user_project_role(request.user, target_column.project)
        if not target_role:
            raise PermissionDenied("Target workspace validation failed.")

        with transaction.atomic():
            Task._base_manager.select_for_update().filter(column=task.column, column_order__gt=task.column_order).update(column_order=F('column_order') - 1)
            Task._base_manager.select_for_update().filter(column=target_column, column_order__gte=new_order).update(column_order=F('column_order') + 1)

            task.column = target_column
            task.column_order = new_order
            task.save(update_fields=['column', 'column_order'])

        return Response({'status': 'Mapped'}, status=status.HTTP_200_OK)