from rest_framework.permissions import BasePermission, SAFE_METHODS

class HierarchicalRolePermission(BasePermission):
    """
    Zero-Trust Security Guard: Programmatically binds standard REST execution structures
    to explicit, app-scoped string permissions evaluated by the hierarchical engine.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Absolute bypass for master system operators
        if request.user.is_superuser:
            return True

        # Derive required app-token boundary strings based on REST verbs
        app_label = 'workspace'
        model_name = getattr(view, 'model_name', 'project')

        if request.method in SAFE_METHODS:
            perm_string = f"{app_label}.view_{model_name}"
        elif request.method == 'POST':
            perm_string = f"{app_label}.add_{model_name}"
        elif request.method in ['PUT', 'PATCH']:
            perm_string = f"{app_label}.change_{model_name}"
        elif request.method == 'DELETE':
            perm_string = f"{app_label}.delete_{model_name}"
        else:
            return False

        return request.user.has_perm(perm_string)