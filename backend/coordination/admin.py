# backend/coordination/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.exceptions import NotRegistered
from .models import Role, UserProfile, Workspace, WorkspaceMembership, Project, ProjectMembership

class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 1
    fields = ('user', 'is_admin')


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'created_by__username')
    list_filter = ('created_at',)
    inlines = [WorkspaceMembershipInline]


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    fields = ('user', 'role')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'workspace', 'created_by', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'workspace__name', 'created_by__username')
    list_filter = ('created_at', 'workspace')
    inlines = [ProjectMembershipInline]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'clearance_weight', 'created_at')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    ordering = ('-clearance_weight',)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Identity RBAC Profile Matrix'
    fk_name = 'user'
    fields = ('role', 'is_verified')


class HardenedUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_select_related = ('profile__role',)

    @admin.display(description='Assigned RBAC Role')
    def get_role(self, instance):
        if hasattr(instance, 'profile') and instance.profile.role:
            return instance.profile.role.name
        return "UNASSIGNED_STUB_IDENTITY"


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, HardenedUserAdmin)