from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from authentication.models import Role

class RoleDAGModelTests(TestCase):
    def setUp(self):
        self.content_type = ContentType.objects.get_for_model(Role)
        self.perm_view = Permission.objects.create(codename='can_view_workspace', name='Can View Workspace', content_type=self.content_type)
        self.perm_edit = Permission.objects.create(codename='can_edit_workspace', name='Can Edit Workspace', content_type=self.content_type)
        
        # Build hierarchy: Level 0 (Root) -> Level 1 (Child)
        self.root_role = Role.objects.create(name='SuperAdmin')
        self.root_role.permissions.add(self.perm_view)
        
        self.child_role = Role.objects.create(name='WorkspaceManager', parent=self.root_role)
        self.child_role.permissions.add(self.perm_edit)

    def test_ancestor_ids_resolution(self):
        """Verifies correct execution path traversal and identification extraction up the hierarchy node array."""
        ancestors = self.child_role.get_ancestor_ids()
        self.assertIn(self.child_role.pk, ancestors)
        self.assertIn(self.root_role.pk, ancestors)
        self.assertEqual(len(ancestors), 2)

    def test_permission_aggregation_queryset(self):
        """Verifies that the concrete object array returned contains both direct and inherited permissions."""
        permissions = self.child_role.get_all_permissions()
        self.assertEqual(permissions.count(), 2)

    def test_permission_strings_flattening(self):
        """Verifies string serialization maps correctly to standard Django 'app_label.codename' formats."""
        perm_strings = self.child_role.get_all_permissions_strings()
        expected_root_perm = f"{self.content_type.app_label}.can_view_workspace"
        expected_child_perm = f"{self.content_type.app_label}.can_edit_workspace"
        self.assertIn(expected_root_perm, perm_strings)
        self.assertIn(expected_child_perm, perm_strings)

    def test_self_referencing_loop_prevention(self):
        """Verifies that a role configuration attempting to reference itself throws a ValidationError."""
        self.root_role.parent = self.root_role
        with self.assertRaises(ValidationError):
            self.root_role.clean()

    def test_deep_circular_reference_prevention(self):
        """Verifies that nested circular loops are trapped by the clean validation walker engine."""
        # Force parent mapping modification directly bypassing initialization constraints
        self.root_role.parent = self.child_role
        with self.assertRaises(ValidationError):
            self.root_role.clean()