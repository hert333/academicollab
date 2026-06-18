# backend/coordination/models.py
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Role(models.Model):
    """
    Unified Hierarchical Role-Based Access Control (RBAC) Data Mapping Matrix.
    """
    name = models.CharField(max_length=50, unique=True)
    clearance_weight = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coordination_roles'
        ordering = ['-clearance_weight']

    def __str__(self):
        return f"{self.name} (Weight: {self.clearance_weight})"


class UserProfile(models.Model):
    """
    Extends core Django user identity vectors to track activation status and RBAC bindings.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'coordination_user_profiles'

    def __str__(self):
        return f"{self.user.username} - Matrix Identity"


class Workspace(models.Model):
    """
    Higher-level organizational tier containing multiple decoupled collaboration projects.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_workspaces'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coordination_workspaces'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WorkspaceMembership(models.Model):
    """
    Tracks explicit user access and administration permissions at the Workspace level.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_memberships'
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    is_admin = models.BooleanField(
        default=False,
        help_text="Designates if the user can manage projects and memberships inside this workspace."
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coordination_workspace_memberships'
        unique_together = [['user', 'workspace']]

    def __str__(self):
        return f"{self.user.username} -> {self.workspace.name} [Admin: {self.is_admin}]"


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coordination_projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ProjectMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='project_memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coordination_project_memberships'
        unique_together = [['user', 'project']]

    def __str__(self):
        return f"{self.user.username} -> {self.project.title} [{self.role.name}]"


class Task(models.Model):
    """
    Unified workflow node. Explicitly linked to Kanban structural layouts and Gantt charts.
    """
    class PriorityChoices(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    column = models.ForeignKey(
        'kanban.KanbanColumn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    priority = models.CharField(
        max_length=15,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        db_index=True
    )
    position = models.IntegerField(
        default=0,
        help_text="Sort sequence within the board column."
    )
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coordination_tasks'
        ordering = ['position', 'created_at']

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'start_date': "Temporal Anomaly: Start date cannot be tracked after the end date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.priority}] {self.title}"


class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='blocked_tasks')

    class Meta:
        db_table = 'coordination_task_dependencies'
        unique_together = [['task', 'depends_on']]

    def clean(self):
        if self.task_id == self.depends_on_id:
            raise ValidationError("Self-Referential loop detected.")
            
        if hasattr(self, 'task') and hasattr(self, 'depends_on'):
            if self.task.project_id != self.depends_on.project_id:
                raise ValidationError("Tenant Isolation Breach.")

        def check_upstream_cycles(current_node_id, target_match_id, visited=None):
            visited = visited or set()
            if current_node_id == target_match_id: 
                return True
            visited.add(current_node_id)
            prereqs = TaskDependency.objects.filter(task_id=current_node_id).values_list('depends_on_id', flat=True)
            for p in prereqs:
                if p not in visited and check_upstream_cycles(p, target_match_id, visited):
                    return True
            return False

        if check_upstream_cycles(self.depends_on_id, self.task_id):
            raise ValidationError("Circular Dependency Volatility.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)