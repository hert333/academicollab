from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from authentication.models import Role, User

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Administrative control plane for managing hierarchical RBAC structures.
    """
    list_display = ('id', 'name', 'parent', 'get_subordinates_count')
    list_filter = ('parent',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    @admin.display(description='Subordinates Count')
    def get_subordinates_count(self, obj):
        return obj.subordinates.count()

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Secure administration panel wrapper for the custom User identity model.
    Guarantees that database password alterations remain properly encrypted.
    """
    list_display = ('id', 'username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    # Injects the custom role selector field into the standard Django User fieldsets mapping
    fieldsets = UserAdmin.fieldsets + (
        (_('Application RBAC Context'), {'fields': ('role',)}),
    )
    
    # Ensures role assignment is accessible during manual admin-driven creation steps
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Application RBAC Context'), {'fields': ('role',)}),
    )