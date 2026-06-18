# backend/kanban/admin.py
from django.contrib import admin
from .models import KanbanColumn
from coordination.models import Task

class KanbanTaskInline(admin.TabularInline):
    model = Task
    extra = 1
    fields = ('title', 'priority', 'start_date', 'end_date', 'position')
    ordering = ('position',)
    # Specify foreign key explicitly to resolve multi-app path tracking
    fk_name = 'column'


@admin.register(KanbanColumn)
class KanbanColumnAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_project_title', 'position')
    list_display_links = ('id', 'name')
    list_filter = ('project',)
    search_fields = ('name', 'project__title')
    ordering = ('project', 'position')
    inlines = [KanbanTaskInline]

    @admin.display(description='Parent Project Context')
    def get_project_title(self, instance):
        return instance.project.title