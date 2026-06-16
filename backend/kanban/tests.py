# backend/kanban/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import Role
from coordination.models import Project, ProjectMembership
from kanban.models import KanbanColumn, Task

User = get_user_model()


class KanbanHierarchicalRBACIntegrationTests(TestCase):
    """
    Architectural Verification Suite: Enforces rigorous validation of the
    IsProjectHierarchicalElement permission policy across different role elevations.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Extract or recreate baseline seeded roles
        cls.member_role, _ = Role.objects.get_or_create(name='MEMBER')
        cls.lead_role, _ = Role.objects.get_or_create(name='LEAD', parent=cls.member_role)
        cls.supervisor_role, _ = Role.objects.get_or_create(name='SUPERVISOR', parent=cls.lead_role)

        # 2. Instantiate isolated user testing nodes
        cls.creator_user = User.objects.create_user(username='creator_user', password='TestPassword123')
        cls.supervisor_user = User.objects.create_user(username='supervisor_user', password='TestPassword123')
        cls.lead_user = User.objects.create_user(username='lead_user', password='TestPassword123')
        cls.member_user = User.objects.create_user(username='member_user', password='TestPassword123')
        cls.external_user = User.objects.create_user(username='external_user', password='TestPassword123')

        # 3. Provision master domain infrastructure elements
        cls.project = Project.objects.create(title='Dissertation Workspace', created_by=cls.creator_user)
        cls.column = KanbanColumn.objects.create(project=cls.project, name='Backlog', order=0)
        cls.task = Task.objects.create(column=cls.column, title='Implement RBAC Core Logic', order=0, assigned_to=cls.member_user)

        # 4. Bind multi-tenant membership mapping records
        ProjectMembership.objects.create(user=cls.supervisor_user, project=cls.project, role=cls.supervisor_role)
        ProjectMembership.objects.create(user=cls.lead_user, project=cls.project, role=cls.lead_role)
        ProjectMembership.objects.create(user=cls.member_user, project=cls.project, role=cls.member_role)

    def setUp(self):
        self.client = APIClient()

    def test_anonymous_and_unauthenticated_requests_are_denied(self):
        """Asserts that unauthenticated traffic is flatly blocked across all mutating endpoints."""
        response = self.client.post('/api/columns/', {'project': str(self.project.id), 'name': 'Blocked Column'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supervisor_has_unrestricted_mutation_privileges(self):
        """Validates that a SUPERVISOR can create architectural elements like columns."""
        self.client.force_authenticate(user=self.supervisor_user)
        response = self.client.post('/api/columns/', {'project': str(self.project.id), 'name': 'In Review', 'order': 1})
        self.assertEqual(
            response.status_code, 
            status.HTTP_201_CREATED, 
            msg=f"DRF Validation Payload Rejection Schema: {response.data}"
        )

    def test_project_lead_has_structural_mutation_privileges(self):
        """Validates that a LEAD can create architectural elements like tasks."""
        self.client.force_authenticate(user=self.lead_user)
        response = self.client.post('/api/tasks/', {'column': self.column.id, 'title': 'Write System Engineering Documentation'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_standard_member_cannot_create_structural_elements(self):
        """Verifies standard members are restricted from appending columns to a project structure."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.post('/api/columns/', {'project': str(self.project.id), 'name': 'Illegal Column Matrix'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_standard_member_can_update_self_assigned_task(self):
        """Verifies standard members retain mutation capacity purely over tasks explicitly assigned to them."""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'title': 'Updated Assignment Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_standard_member_cannot_update_unassigned_tasks(self):
        """Asserts members are structurally blocked from modifying tasks where they are not designated owners."""
        unassigned_task = Task.objects.create(column=self.column, title='Foreign Task Context', order=1, assigned_to=self.lead_user)
        self.client.force_authenticate(user=self.member_user)
        response = self.client.patch(f'/api/tasks/{unassigned_task.id}/', {'title': 'Malicious Intervention Attempt'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_workspace_user_completely_blocked(self):
        """Ensures authenticated application users lacking workspace scopes are rejected."""
        self.client.force_authenticate(user=self.external_user)
        response_mutation = self.client.patch(f'/api/tasks/{self.task.id}/', {'title': 'External Shift'})
        self.assertEqual(response_mutation.status_code, status.HTTP_403_FORBIDDEN)