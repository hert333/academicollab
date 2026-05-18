from django.db import models
from django.contrib.auth.models import AbstractUser, Permission

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subordinates'
    )
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name

    def get_all_permissions(self):
        """
        Recursively traverses upward through the role hierarchy to compile 
        an aggregated set of all inherited permissions.
        """
        perms = set(self.permissions.all())
        if self.parent:
            perms.update(self.parent.get_all_permissions())
        return perms

class User(AbstractUser):
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='users'
    )

    def has_perm(self, perm, obj=None):
        """
        Overrides core authentication checks to pass authorization queries 
        directly through the hierarchical permission tree.
        """
        if self.is_active and self.is_superuser:
            return True
        
        if not self.role:
            return False
            
        parsed_perm = perm.split('.')[-1]
        inherited_perms = self.role.get_all_permissions()
        
        return any(p.codename == parsed_perm for p in inherited_perms)