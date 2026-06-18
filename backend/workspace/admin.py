# workspace/admin.py
from django.contrib import admin
from .models import Project, Task

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Administrative control dashboard for AcademiCollab workspace ecosystems.
    Provides direct multi-tenant visualization and filtering structures.
    """
    list_display = ('id', 'name', 'created_by', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'created_by__username', 'created_by__email')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    
    # Auto-populate user record with current authenticated session operator during manual admin creation
    def save_model(self, request, obj, form, change):
        if not change or not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Task administration gate tracking Kanban states, ordering indices, 
    and recursive Gantt layout timeline blocks.
    """
    list_display = (
        'id', 
        'title', 
        'project', 
        'status', 
        'order', 
        'assigned_to', 
        'start_date', 
        'end_date', 
        'get_dependency'
    )
    list_display_links = ('id', 'title')
    list_filter = ('status', 'project', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'assigned_to__username', 'project__name')
    ordering = ('project', 'status', 'order')
    list_editable = ('status', 'order')
    
    raw_id_fields = ('assigned_to', 'depends_on', 'project')
    
    fieldsets = (
        ('Core Scope', {
            'fields': ('project', 'title', 'description')
        }),
        ('Kanban Layout State', {
            'fields': ('status', 'order', 'assigned_to')
        }),
        ('Gantt Engine Timelines & Blocks', {
            'fields': ('start_date', 'end_date', 'depends_on')
        }),
    )

    @admin.display(ordering='depends_on__title', description='Blocking Task Dependency')
    def get_dependency(self, obj):
        """ Renders the exact title of the linked upward block requirement if present. """
        if obj.depends_on:
            return f"#{obj.depends_on.id} - {obj.depends_on.title}"
        return "None"

    def get_queryset(self, request):
        """ Optimizes data collection using select_related to eliminate database N+1 queries. """
        return super().get_queryset(request).select_related('project', 'assigned_to', 'depends_on')