# workspace/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import Role
from coordination.models import ProjectMembership, Project as CoordinationProject
from workspace.models import Project as WorkspaceProject, Task

User = get_user_model()


class WorkspaceIntegrationAndRBACVerifyTests(TestCase):
    """
    Architectural Verification Suite: Enforces multi-tenant data boundaries,
    hierarchical role constraints, and batch Kanban mutations for the Workspace layer
    using correctly resolved cross-app model boundaries.
    """

    @classmethod
    def setUpTestData(cls):
        # 1. Establish baseline system operational roles
        cls.member_role, _ = Role.objects.get_or_create(name='MEMBER')
        cls.lead_role, _ = Role.objects.get_or_create(name='LEAD', parent=cls.member_role)
        cls.supervisor_role, _ = Role.objects.get_or_create(name='SUPERVISOR', parent=cls.lead_role)

        # 2. Instantiate decoupled testing users
        cls.creator_user = User.objects.create_user(username='creator', password='TestPassword123')
        cls.supervisor_user = User.objects.create_user(username='supervisor', password='TestPassword123')
        cls.lead_user = User.objects.create_user(username='lead', password='TestPassword123')
        cls.member_user = User.objects.create_user(username='member', password='TestPassword123')
        cls.external_user = User.objects.create_user(username='external', password='TestPassword123')

        # 3. Provision workspace infrastructure nodes with matching relational targets
        # Core coordination project used for ProjectMembership constraints
        cls.coordination_project = CoordinationProject.objects.create(title='Dissertation Core Workspace', created_by=cls.creator_user)
        
        # Workspace project matching the database ID for endpoint validation
        cls.workspace_project = WorkspaceProject.objects.create(
            id=cls.coordination_project.id,
            name=cls.coordination_project.title,
            created_by=cls.creator_user
        )
        
        cls.task_assigned = Task.objects.create(
            project=cls.workspace_project,
            title='Develop Frontend Visualization View',
            status='TODO',
            order=0,
            assigned_to=cls.member_user
        )
        
        cls.task_unassigned = Task.objects.create(
            project=cls.workspace_project,
            title='Configure CI/CD Enterprise Pipeline',
            status='TODO',
            order=1,
            assigned_to=cls.lead_user
        )

        # 4. Bind multi-tenant membership mapping records using the correct coordination project target
        ProjectMembership.objects.create(user=cls.supervisor_user, project=cls.coordination_project, role=cls.supervisor_role)
        ProjectMembership.objects.create(user=cls.lead_user, project=cls.coordination_project, role=cls.lead_role)
        ProjectMembership.objects.create(user=cls.member_user, project=cls.coordination_project, role=cls.member_role)

    def setUp(self):
        self.client = APIClient()

    def _get_project_detail_url(self, project_id):
        return f'/api/workspace/projects/{project_id}/'

    def _get_task_detail_url(self, task_id):
        return f'/api/workspace/tasks/{task_id}/'

    def test_unauthenticated_traffic_is_unconditionally_denied(self):
        """ Assures unauthenticated requests fail with an explicit 401 response code. """
        response = self.client.get('/api/workspace/projects/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_external_authenticated_user_cannot_access_tenant(self):
        """ Verifies users outside the project workspace cannot fetch its data (403). """
        self.client.force_authenticate(user=self.external_user)
        response = self.client.get(self._get_project_detail_url(self.workspace_project.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_mutate_self_assigned_task(self):
        """ Verifies standard members can modify tasks assigned to them. """
        self.client.force_authenticate(user=self.member_user)
        url = self._get_task_detail_url(self.task_assigned.id)
        response = self.client.patch(url, {'title': 'Updated Owned Assignment'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_blocked_from_mutating_unassigned_task(self):
        """ Verifies standard members are blocked from changing tasks they do not own. """
        self.client.force_authenticate(user=self.member_user)
        url = self._get_task_detail_url(self.task_unassigned.id)
        response = self.client.patch(url, {'title': 'Malicious Intervention Attempt'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_lead_can_mutate_any_workspace_task(self):
        """ Verifies LEAD role identities can alter any task within their workspace. """
        self.client.force_authenticate(user=self.lead_user)
        url = self._get_task_detail_url(self.task_assigned.id)
        response = self.client.patch(url, {'title': 'Lead Structural Refactor Override'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_batch_kanban_reorder_safeguards_tenant_boundaries(self):
        """ Assures that bulk reordering prevents processing foreign task IDs. """
        self.client.force_authenticate(user=self.member_user)
        payload = {
            "task_orders": [
                {"id": self.task_assigned.id, "order": 5, "status": "IN_PROGRESS"},
                {"id": 99999, "order": 1, "status": "TODO"}  # Malformed / Out-of-bounds context ID
            ]
        }
        response = self.client.post('/api/workspace/tasks/reorder-kanban/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_batch_kanban_reorder_success(self):
        """ Validates transactional batch adjustments for authorized project tasks. """
        self.client.force_authenticate(user=self.lead_user)
        payload = {
            "task_orders": [
                {"id": self.task_assigned.id, "order": 1, "status": "REVIEW"},
                {"id": self.task_unassigned.id, "order": 0, "status": "IN_PROGRESS"}
            ]
        }
        response = self.client.post('/api/workspace/tasks/reorder-kanban/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes persisted to the database
        self.task_assigned.refresh_from_db()
        self.task_unassigned.refresh_from_db()
        self.assertEqual(self.task_assigned.status, "REVIEW")
        self.assertEqual(self.task_unassigned.status, "IN_PROGRESS")