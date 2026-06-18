# backend/authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from authentication.models import Role, User

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Administrative control plane for managing hierarchical RBAC structures.
    Optimized with select_related to eliminate N+1 query overhead.
    """
    list_display = ('id', 'name', 'parent', 'get_subordinates_count')
    list_filter = ('parent',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')

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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('role')
        
    fieldsets = UserAdmin.fieldsets + (
        (_('Application RBAC Context'), {'fields': ('role',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Application RBAC Context'), {'fields': ('role',)}),
    )