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
            admin_role = RoleModel.objects.filter(name__icontains='admin').first() or RoleModel.objects.first()
            if admin_role:
                extra_fields.setdefault('role', admin_role)
        except (LookupError, Exception):
            pass

        return self.create_user(username, email, password, **extra_fields)


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
        """
        FIXED: Contract Requirement for the Serialization layer.
        Resolves and returns a distinct QuerySet of concrete Permission object instances 
        inherited through the role lineage graph.
        """
        ancestor_ids = self.get_ancestor_ids()
        return Permission.objects.filter(role__id__in=ancestor_ids).distinct()

    def get_all_permissions_strings(self):
        """
        Flattens permission query evaluation. Compiles exact 'app_label.codename' 
        strings using a single batch database transaction.
        """
        ancestor_ids = self.get_ancestor_ids()
        return set(
            Permission.objects.filter(role__id__in=ancestor_ids)
            .values_list('content_type__app_label', 'codename')
            .annotate(full_perm=models.functions.Concat(
                'content_type__app_label', models.Value('.'), 'codename'
            ))
            .values_list('full_perm', flat=True)
        )


class User(AbstractUser):
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name='users'
    )

    objects = CustomUserManager()

    def has_perm(self, perm, obj=None):
        """
        Evaluates qualified authentication checks ('app_label.codename') against 
        the flattened hierarchical role array.
        """
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if not self.role:
            return False

        return perm in self.role.get_all_permissions_strings()

    def has_module_perms(self, app_label):
        """
        Required override ensuring Django Administrative interface maps access controls 
        accurately against hierarchical structures.
        """
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