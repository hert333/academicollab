from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from authentication.models import Role

class Command(BaseCommand):
    help = 'Seeds initial hierarchical academic roles and base permissions cleanly'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database synchronization pass...')

        # FIXED: Enforce absolute database transaction bounds to prevent partial state corruption
        try:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(Role)
                
                # Instantiate granular system authorization boundaries cleanly
                perm_view_dashboard, _ = Permission.objects.get_or_create(
                    codename='can_view_dashboard',
                    content_type=content_type,
                    defaults={'name': 'Can View Dashboard'}
                )
                perm_edit_milestones, _ = Permission.objects.get_or_create(
                    codename='can_edit_milestones',
                    content_type=content_type,
                    defaults={'name': 'Can Edit High-Level Milestones'}
                )

                # FIXED: Enforce idempotency and parent-node reconciliation down the tree hierarchy
                supervisor_role, _ = Role.objects.get_or_create(name='Supervisor', defaults={'parent': None})
                if supervisor_role.parent is not None:
                    supervisor_role.parent = None
                    supervisor_role.save()
                supervisor_role.permissions.add(perm_edit_milestones)

                pm_role, _ = Role.objects.get_or_create(name='Project Manager', defaults={'parent': supervisor_role})
                if pm_role.parent != supervisor_role:
                    pm_role.parent = supervisor_role
                    pm_role.save()
                pm_role.permissions.add(perm_view_dashboard)

                student_role, _ = Role.objects.get_or_create(name='Student', defaults={'parent': pm_role})
                if student_role.parent != pm_role:
                    student_role.parent = pm_role
                    student_role.save()

            self.stdout.write(self.style.SUCCESS('Successfully synchronized Supervisor -> PM -> Student hierarchy.'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'CRITICAL FAILURE DURING SEED EXECUTION: {str(e)}'))
            raise e