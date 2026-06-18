# workspace/permissions.py
from django.http import Http404
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied

# Cross-App model discovery layout to resolve multi-tenant roles dynamically
from coordination.models import ProjectMembership
from .models import Project, Task

def get_user_project_role(user, project):
    """
    Direct relational lookup determining the user's operational role 
    within the target project workspace boundaries.
    """
    if not user or user.is_anonymous or not project:
        return None
    membership = ProjectMembership._base_manager.filter(user=user, project=project).select_related('role').first()
    if membership and membership.role:
        return membership.role.name.upper()
    return None


class WorkspaceHierarchicalRBACPermission(BasePermission):
    """
    Enforces security boundaries for AcademiCollab Workspace and Task elements.
    Guarantees that access is limited to authorized workspace members.
    """

    def has_permission(self, request, view):
        # Enforce baseline global authentication
        if not request.user or not request.user.is_authenticated:
            return False

        view_class = getattr(view, 'basename', None) or view.__class__.__name__

        # 1. Intercept Task and Project Collection Creation (POST)
        if request.method == 'POST':
            # Anyone authenticated can create a brand new Project workspace
            if 'Project' in view_class or view_class == 'project':
                return True

            # Task creations require a target project identity check inside the payload
            if 'Task' in view_class or view_class == 'task':
                project_id = request.data.get('project')
                if not project_id:
                    return True # Delegate to serializer level validation for missing fields
                
                project = Project._base_manager.filter(id=project_id).first()
                if not project:
                    raise Http404("Target project workspace does not exist.")
                
                role = get_user_project_role(request.user, project)
                if not role or role not in ['SUPERVISOR', 'LEAD', 'MEMBER']:
                    raise PermissionDenied("You do not belong to this project workspace ecosystem.")
                return True

        # For safe methods or detail operations, allow routing down to object checks or queryset filters
        return True

    def has_object_permission(self, request, view, obj):
        """
        Enforces contextual role logic for specific instance records.
        """
        # Resolve target project reference based on instance class type
        if isinstance(obj, Project):
            target_project = obj
        elif isinstance(obj, Task):
            target_project = obj.project
        else:
            return False

        # Extract explicit role matrix for current authenticated user context
        role = get_user_project_role(request.user, target_project)

        # 1. Read Operations (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            if role or (isinstance(obj, Project) and obj.created_by == request.user):
                return True
            raise PermissionDenied("Access to this workspace ecosystem is denied.")

        # 2. Structural Modification Operations (PUT, PATCH, DELETE)
        if isinstance(obj, Project):
            # Only Project Creator, Workspace SUPERVISOR, or LEAD can alter project properties
            if obj.created_by == request.user or (role in ['SUPERVISOR', 'LEAD']):
                return True
            raise PermissionDenied("You do not have administrative permissions for this workspace.")

        if isinstance(obj, Task):
            # Administrative layers have complete mutation rights over tasks
            if role in ['SUPERVISOR', 'LEAD']:
                return True
            # Standard Members can only edit tasks explicitly assigned to them
            if role == 'MEMBER' and obj.assigned_to == request.user:
                return True
            
            raise PermissionDenied("Standard members are blocked from mutating tasks they do not own.")

        return False