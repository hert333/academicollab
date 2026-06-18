# backend/workspace/models.py
from django.db import models
from django.conf import settings

class Workspace(models.Model):
    """
    Top-level Multi-Tenant Academic Environment Partition.
    Acts as the parent boundary cluster for projects, kanban instances, and research groups.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workspace_created_environments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workspace_node'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Project(models.Model):
    """
    API Model managing multi-tenant Project workspaces.
    Mounted directly inside a parenting Academic Environment Node block.
    """
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,  # Preserves migration safety matrix for existing row entries
        blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # PRESERVED: App-prefixed unique reverse namespace
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='workspace_created_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workspace_project'

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    API Model managing individual Task workflows, Kanban column positions, 
    and Gantt timeline dependency linkages.
    """
    class StatusChoices(models.TextChoices):
        BACKLOG = 'BACKLOG', 'Backlog'
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        REVIEW = 'REVIEW', 'In Review'
        DONE = 'DONE', 'Done'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.TODO)
    order = models.PositiveIntegerField(default=0, help_text="Tracks position order inside the specific Kanban column layer.")
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    depends_on = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='blocked_tasks'
    )
    
    # PRESERVED: App-prefixed unique reverse namespace
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='workspace_assigned_tasks'
    )

    class Meta:
        db_table = 'workspace_task'
        ordering = ['order']

    def __str__(self):
        return f"[{self.project.name}] {self.title} - {self.status}"