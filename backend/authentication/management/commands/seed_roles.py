# backend/authentication/management/commands/seed_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from authentication.models import Role

class Command(BaseCommand):
    help = 'Seeds initial hierarchical normalized academic roles and permissions cleanly'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database synchronization pass...')

        try:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(Role)
                
                # Granular security boundary parameters
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

                # Normalized absolute uppercase keys matching frontend and JWT vectors
                admin_role, _ = Role.objects.get_or_create(name='ADMIN', defaults={'parent': None})
                if admin_role.parent is not None:
                    admin_role.parent = None
                    admin_role.save()
                admin_role.permissions.add(perm_view_dashboard, perm_edit_milestones)

                supervisor_role, _ = Role.objects.get_or_create(name='SUPERVISOR', defaults={'parent': admin_role})
                if supervisor_role.parent != admin_role:
                    supervisor_role.parent = admin_role
                    supervisor_role.save()
                supervisor_role.permissions.add(perm_edit_milestones)

                faculty_role, _ = Role.objects.get_or_create(name='FACULTY', defaults={'parent': supervisor_role})
                if faculty_role.parent != supervisor_role:
                    faculty_role.parent = supervisor_role
                    faculty_role.save()
                faculty_role.permissions.add(perm_view_dashboard)

                student_role, _ = Role.objects.get_or_create(name='STUDENT', defaults={'parent': faculty_role})
                if student_role.parent != faculty_role:
                    student_role.parent = faculty_role
                    student_role.save()

            self.stdout.write(self.style.SUCCESS('Successfully synchronized normalized hierarchy: ADMIN -> SUPERVISOR -> FACULTY -> STUDENT.'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'CRITICAL FAILURE DURING SEED EXECUTION: {str(e)}'))
            raise e