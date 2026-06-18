# backend/authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, BaseUserManager
from django.core.exceptions import ValidationError
from django.apps import apps


class CustomUserManager(BaseUserManager):
    """
    Architectural Guard: Automatically binds the highest available administrative
    role to superusers provisioned via CLI management commands.
    """
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        try:
            RoleModel = apps.get_model('authentication', 'Role')
            # Look up normalized absolute uppercase key explicitly
            admin_role = RoleModel.objects.filter(name='ADMIN').first() or RoleModel.objects.first()
            if admin_role:
                extra_fields.setdefault('role', admin_role)
        except (LookupError, Exception):
            pass

        return self.create_user(username, email, password, **extra_fields)


class Role(models.Model):
    """
    Represents a system role within a directed acyclic graph (DAG) structure.
    """
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
        """
        Enforces strict directed acyclic graph (DAG) invariants.
        Prevents self-referencing loops during instance mutation.
        """
        super().clean()
        if self.parent_id and self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Loop detected: A role cannot become a subordinate of itself."})
            
        visited = {self.pk} if self.pk else set()
        current_parent = self.parent
        while current_parent:
            if current_parent.pk in visited:
                raise ValidationError({"parent": f"Circular reference detected: '{current_parent.name}' creates an infinite loop."})
            if current_parent.pk:
                visited.add(current_parent.pk)
            current_parent = current_parent.parent

    def save(self, *args, **kwargs):
        """Intercepts saving events to guarantee full execution of loop validation limits."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_ancestor_ids(self):
        """
        Traverses hierarchy in-memory via foreign key caches to collect ancestor IDs.
        Defensively tracks visited objects to eliminate runtime infinite loops.
        """
        ancestor_ids = []
        if self.pk:
            ancestor_ids.append(self.pk)
            
        visited = set(ancestor_ids)
        current = self
        while current.parent_id and current.parent_id not in visited:
            ancestor_ids.append(current.parent_id)
            visited.add(current.parent_id)
            current = current.parent
        return ancestor_ids

    def get_all_permissions(self):
        """Resolves distinct QuerySet of Permission object instances inherited through lineage."""
        ancestor_ids = self.get_ancestor_ids()
        return Permission.objects.filter(role__id__in=ancestor_ids).distinct()

    def get_all_permissions_strings(self):
        """Flattens permission query evaluation into a set of 'app_label.codename' fields."""
        ancestor_ids = self.get_ancestor_ids()
        return set(
            Permission.objects.filter(role__id__in=ancestor_ids)
            .annotate(full_perm=models.functions.Concat(
                'content_type__app_label', models.Value('.'), 'codename'
            ))
            .values_list('full_perm', flat=True)
        )


class User(AbstractUser):
    """Custom user model integrating the hierarchical global system role."""
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='users'
    )

    objects = CustomUserManager()

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return perm in self.role.get_all_permissions_strings()

    def has_module_perms(self, app_label):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if not self.role:
            return False

        ancestor_ids = self.role.get_ancestor_ids()
        return Permission.objects.filter(
            role__id__in=ancestor_ids, 
            content_type__app_label=app_label
        ).exists()