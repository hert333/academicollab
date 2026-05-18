from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from authentication.models import Role

class Command(BaseCommand):
    help = 'Seeds initial hierarchical academic roles and base permissions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding roles...')

        content_type = ContentType.objects.get_for_model(Role)
        
        perm_view_dashboard, _ = Permission.objects.get_or_create(
            codename='can_view_dashboard',
            name='Can View Dashboard',
            content_type=content_type,
        )
        perm_edit_milestones, _ = Permission.objects.get_or_create(
            codename='can_edit_milestones',
            name='Can Edit High-Level Milestones',
            content_type=content_type,
        )

        supervisor_role, _ = Role.objects.get_or_create(name='Supervisor', parent=None)
        supervisor_role.permissions.add(perm_edit_milestones)

        pm_role, _ = Role.objects.get_or_create(name='Project Manager', parent=supervisor_role)
        pm_role.permissions.add(perm_view_dashboard)

        student_role, _ = Role.objects.get_or_create(name='Student', parent=pm_role)

        self.stdout.write(self.style.SUCCESS('Successfully seeded Supervisor -> PM -> Student hierarchy.'))
