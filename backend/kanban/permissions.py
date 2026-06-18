# backend/kanban/permissions.py
from rest_framework import permissions
from django.apps import apps

class IsProjectHierarchicalElement(permissions.BasePermission):
    """
    Zero-Trust Hierarchical Access Controller:
    Validates user workspace membership and enforces granular role privileges.
    Bypasses compile-time circular dependency loops via runtime lazy application registry lookups.
    """

    def _get_models(self):
        """Lazy lookup engine to completely bypass Django circular imports."""
        Project = apps.get_model('coordination', 'Project')
        ProjectMembership = apps.get_model('coordination', 'ProjectMembership')
        KanbanColumn = apps.get_model('kanban', 'KanbanColumn')
        return Project, ProjectMembership, KanbanColumn

    def get_project_from_request(self, request, view):
        Project, _, KanbanColumn = self._get_models()
        
        # 1. Safely pull model dependencies out of URL keywords without calling view.get_object()
        if 'pk' in view.kwargs:
            try:
                # Deduce the database layer depending on what ViewSet is being triggered
                if view.basename == 'kanban-columns':
                    return KanbanColumn.objects.get(id=view.kwargs['pk']).project
                if view.basename == 'kanban-tasks':
                    Task = apps.get_model('kanban', 'Task')
                    return Task.objects.get(id=view.kwargs['pk']).column.project
            except Exception:
                return None
        
        # 2. Extract context from POST/PUT request bodies
        if request.method in ['POST', 'PUT', 'PATCH']:
            project_id = request.data.get('project')
            if project_id:
                try:
                    return Project.objects.get(id=project_id)
                except (Project.DoesNotExist, ValueError):
                    return None
            
            column_id = request.data.get('column')
            if column_id:
                try:
                    return KanbanColumn.objects.get(id=column_id).project
                except (KanbanColumn.DoesNotExist, ValueError):
                    return None
                    
        return None

    def has_permission(self, request, view):
        # Enforce global authentication barrier
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # For list actions, views filter their queries by tenant boundary natively
        if view.action == 'list':
            return True

        project = self.get_project_from_request(request, view)
        if not project:
            # If checking an instance mutation, defer to object-level hook execution (has_object_permission)
            return 'pk' in view.kwargs

        _, ProjectMembership, _ = self._get_models()
        try:
            membership = ProjectMembership.objects.get(user=request.user, project=project)
        except ProjectMembership.DoesNotExist:
            return False

        role_name = membership.role.name.upper()

        # Structural manipulation restriction: Only LEAD, SUPERVISOR, or ADMIN can append columns
        if view.basename == 'kanban-columns' and request.method == 'POST':
            return role_name in ['LEAD', 'SUPERVISOR', 'ADMIN']

        # Task appending constraints: MEMBER, LEAD, SUPERVISOR, or ADMIN are allowed
        if view.basename == 'kanban-tasks' and request.method == 'POST':
            return role_name in ['MEMBER', 'LEAD', 'SUPERVISOR', 'ADMIN']

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        Project, ProjectMembership, _ = self._get_models()
        
        # Extract project context safely based on object type introspection
        if isinstance(obj, Project):
            project = obj
        elif hasattr(obj, 'project'):
            project = obj.project
        elif hasattr(obj, 'column'):
            project = obj.column.project
        else:
            return False
        
        try:
            membership = ProjectMembership.objects.get(user=request.user, project=project)
        except ProjectMembership.DoesNotExist:
            return False

        role_name = membership.role.name.upper()

        # SUPERVISOR, LEAD, and ADMIN retain global mutation access over workspace elements
        if role_name in ['LEAD', 'SUPERVISOR', 'ADMIN']:
            return True

        # MEMBER mutation boundary: restricted to tasks explicitly assigned to them
        if role_name == 'MEMBER' and hasattr(obj, 'assigned_to'):
            return obj.assigned_to == request.user

        return False