from django.db import models

# Create your models here.
# backend/kanban/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def default_start_date():
    return timezone.now().date()

def default_due_date():
    return (timezone.now() + timedelta(days=7)).date()

class Board(models.Model):
    """
    Tethers Kanban tracking layers to distinct academic project clusters.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Column(models.Model):
    """
    Represents structural workflow phases (e.g., Backlog, In Progress, Review, Done).
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(help_text="The sequence location weight index.")

    class Meta:
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(fields=['board', 'position'], name='unique_column_position_per_board')
        ]

    def __str__(self):
        return f"{self.board.name} -> {self.name} ({self.position})"


class Task(models.Model):
    """
    Operational unit of execution inside AcademiCollab tracking frameworks.
    """
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    position = models.PositiveIntegerField(help_text="Index orientation weight within a column cluster.")
    priority = models.CharField(max_length=12, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Context-linked relational metrics mapping back to authentication architecture
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_kanban_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_kanban_tasks'
    )
    
    start_date = models.DateField(default=default_start_date)
    due_date = models.DateField(default=default_due_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Task #{self.id}: {self.title} (Col: {self.column.name})"