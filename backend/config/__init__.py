import os

# FIXED: Explicitly bind the Celery task application to the Django lifecycle namespace
# This guarantees that shared background tasks for Kanban/Gantt calculations load automatically on startup.
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Fallback to prevent bootstrap blocks if celery setup is decoupled during initial migrations
    __all__ = ()