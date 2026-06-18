# backend/kanban/models.py
from django.db import models
from coordination.models import Project

class KanbanColumn(models.Model):
    """
    Configuration layer for vertical board stages.
    """
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='kanban_columns'
    )
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(
        default=0,
        help_text="Visual ordering parameter from left to right."
    )

    class Meta:
        db_table = 'kanban_columns'
        ordering = ['position']

    def __str__(self):
        return f"{self.project.title} - {self.name}"