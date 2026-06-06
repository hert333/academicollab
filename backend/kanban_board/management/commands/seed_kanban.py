# backend/kanban_board/management/commands/seed_kanban.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kanban_board.models import Board, Column, Task

User = get_user_model()

class Command(BaseCommand):
    help = 'Idempotently seeds database layers with complete HCI asset sets.'

    def handle(self, *args, **options):
        # Enforce administrative configuration entity existence
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@academicollab.local',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if _:
            user.set_password('admin123')
            user.save()

        # Enforce workspace instance mapping existence
        board, board_created = Board.objects.get_or_create(
            name='AcademiCollab Dissertation Workspace',
            defaults={'description': 'System engineering tracking framework for 3-tier decoupled execution model.'}
        )
        
        self.stdout.write(self.style.SUCCESS(f'TARGET BOARD IDENTIFIER VALUE: {board.id}'))

        # Standard lane layout definitions
        lanes = ['Backlog', 'To Do', 'In Progress', 'In Review', 'Done']
        columns_map = {}
        
        # Sync structural columns loops independently
        for position, name in enumerate(lanes):
            col, col_created = Column.objects.get_or_create(
                board=board,
                name=name,
                defaults={'position': position}
            )
            columns_map[name] = col
            if col_created:
                self.stdout.write(self.style.SUCCESS(f"Synchronized column lane: [{name}]"))

        # Explicit task records definitions 
        sample_tasks = [
            ('Configure Zero-Trust JWT Middleware', 'Isolate routes behind backend server validation layers.', 'CRITICAL', columns_map['To Do']),
            ('Verify HCI Dynamic Layout Bounds', 'Test viewport rendering stability with high concurrency counts.', 'HIGH', columns_map['In Progress']),
            ('Validate Idempotency Locks', 'Confirm database state engine blocks transactional duplication.', 'MEDIUM', columns_map['Backlog']),
        ]

        # Sync operational tasks structures
        for idx, (title, desc, priority, col) in enumerate(sample_tasks):
            task, task_created = Task.objects.get_or_create(
                column=col,
                title=title,
                defaults={
                    'description': desc,
                    'priority': priority,
                    'assigned_to': user,
                    'position': idx
                }
            )
            if task_created:
                self.stdout.write(self.style.SUCCESS(f"Injected operational task item: {title}"))

        self.stdout.write(self.style.SUCCESS('Database synchronization completed successfully.'))