from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.core.exceptions import ValidationError

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

    def clean(self):
        # Prevent manual cyclic parent assignment loops before database serialization
        super().clean()
        parent_node = self.parent
        while parent_node is not None:
            if parent_node.pk == self.pk:
                raise ValidationError({"parent": "Loop detected: A role cannot become a subordinate of itself."})
            parent_node = parent_node.parent

    def get_all_permissions(self, visited=None):
        """
        Recursively compiles an aggregated set of inherited permissions.
        Guarded against cyclic path traps using local identity tracking.
        """
        if visited is None:
            visited = set()
            
        if self.pk in visited:
            return set()
            
        visited.add(self.pk)
        perms = set(self.permissions.all())
        
        if self.parent:
            perms.update(self.parent.get_all_permissions(visited))
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
        Evaluates system authorization requirements against the active hierarchical tree.
        Supports both qualified names and localized app-agnostic strings.
        """
        if self.is_active and self.is_superuser:
            return True
        if not self.role:
            return False
            
        # Extracts raw codename while providing support for complete workspace strings
        codename = perm.split('.')[-1]
        inherited_perms = self.role.get_all_permissions()
        
        return any(p.codename == codename for p in inherited_perms)