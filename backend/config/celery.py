import os
from celery import Celery

# FIXED: Realigned the baseline orchestration environment parameter to target your config subfolder
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('academicollab')

# FIXED: Encapsulate all configuration keys behind a uniform namespace prefix to prevent system parameter collisions
# All celery tracking config keys must be declared in settings.py with a 'CELERY_' identifier prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# FIXED: Configure explicit runtime task exploration sweeps across all active registered Django app folders
# This ensures that files named 'tasks.py' inside your architecture apps are parsed and bound automatically.
app.autodiscover_tasks()


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def debug_task(self):
    """
    Foundational verification task used to evaluate background container pipeline connectivity.
    """
    print(f'Execution verification confirmation checkpoint. Request Metadata ID: {self.request.id!r}')