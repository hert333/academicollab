# backend/kanban/migrations/0001_initial.py
# Generated manually to remediate multi-tenant domain duplication

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('coordination', '0001_initial'),  # Ensures coordination tables exist first
    ]

    operations = [
        migrations.CreateModel(
            name='KanbanColumn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('order', models.PositiveIntegerField(default=0, help_text="Maintains the horizontal position sequence of the column pipeline.")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kanban_columns', to='coordination.project')),
            ],
            options={
                'db_table': 'kanban_columns',
                'ordering': ['order'],
                # Decoupled database-level unique constraints to prevent write-locks during reordering
            },
        ),
    ]