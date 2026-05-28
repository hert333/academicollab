import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Project(models.Model):
    """
    Delineates the top-level collaborative research boundaries within AcademiCollab.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class Task(models.Model):
    """
    Represents a singular workflow node. Serves as a Kanban card component 
    and a Gantt timeline node simultaneously.
    """
    class StatusChoices(models.TextChoices):
        BACKLOG = 'BACKLOG', 'Backlog'
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        REVIEW = 'REVIEW', 'Review'
        DONE = 'DONE', 'Done'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Kanban State Tracking Elements
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.TODO,
        db_index=True
    )
    column_order = models.IntegerField(
        default=0,
        help_text="Maintains layout sort sequence for drag-and-drop updates inside the same column state."
    )
    
    # Gantt Timeline Tracking Matrix Elements
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
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
        ordering = ['column_order', 'created_at']
        # Guarantees that order indexes don't conflict across identical state scopes
        unique_together = [['project', 'status', 'column_order']]

    def clean(self):
        """
        Validates timeline logic sanity before passing data execution down to PostgreSQL.
        """
        if self.start_date and self.due_date:
            if self.start_date > self.due_date:
                raise ValidationError({
                    'start_date': "Temporal Anomaly: Task start_date cannot be set after its defined due_date."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.status}] {self.title}"


class TaskDependency(models.Model):
    """
    Models the Directed Acyclic Graph (DAG) required to map task prerequisites 
    and calculate critical paths for Gantt visualizations.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependencies'
    )
    depends_on = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='blocked_tasks'
    )

    class Meta:
        db_table = 'coordination_task_dependencies'
        unique_together = [['task', 'depends_on']]

    def clean(self):
        """
        Enforces defensive rules directly on the schema configuration to prevent infinite evaluation loops.
        """
        if self.task_id == self.depends_on_id:
            raise ValidationError("Self-Referential loop detected: A task cannot be dependent on itself.")
        
        # Validates basic circular dependency patterns
        if TaskDependency.objects.filter(task=self.depends_on, depends_on=self.task).exists():
            raise ValidationError("Circular Dependency Volatility: Upstream tracking collision detected.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task.title} depends on {self.depends_on.title}"