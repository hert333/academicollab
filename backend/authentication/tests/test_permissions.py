# backend/authentication/tests/test_permissions.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import Role, User

class HierarchicalRBACSecurityTests(APITestCase):

    def setUp(self):
        """
        Set up isolated structural nodes for roles and users matching the hierarchy.
        """
        # Build foundational Role instances
        self.student_role = Role.objects.create(name='Student')
        self.pm_role = Role.objects.create(name='Project Manager')
        self.supervisor_role = Role.objects.create(name='Supervisor')
        self.admin_role = Role.objects.create(name='Admin')

        # Generate targeted User profiles
        self.student_user = User.objects.create_user(
            username='student_node', email='student@domain.local', password='password123', role=self.student_role
        )
        self.supervisor_user = User.objects.create_user(
            username='supervisor_node', email='supervisor@domain.local', password='password123', role=self.supervisor_role
        )
        self.admin_user = User.objects.create_user(
            username='admin_node', email='admin@domain.local', password='password123', role=self.admin_role
        )

        # Endpoint target lookup for UserViewSet detail modifications
        self.target_url = reverse('user-detail', kwargs={'pk': self.student_user.id})

    def test_student_token_blocked_from_role_mutation_via_patch(self):
        """
        CRITICAL VULNERABILITY MITIGATION ASSERTION:
        Asserts that a Student token executing a PATCH request is blocked from escalating privileges.
        """
        self.client.force_authenticate(user=self.student_user)
        payload = {"role": self.admin_role.id}
        
        response = self.client.patch(self.target_url, payload, format='json')
        
        # Must return 400 Bad Request due to validation exception or 403 Forbidden via permission class
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_supervisor_token_blocked_from_role_mutation_via_patch(self):
        """
        Asserts that a Supervisor can view/manage users but cannot change roles to Admin.
        """
        self.client.force_authenticate(user=self.supervisor_user)
        payload = {"role": self.admin_role.id}
        
        response = self.client.patch(self.target_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('role', response.data)

    def test_admin_token_authorized_to_mutate_roles(self):
        """
        Asserts that a valid Admin account is permitted to reassign structural role metrics.
        """
        self.client.force_authenticate(user=self.admin_user)
        payload = {"role": self.pm_role.id}
        
        response = self.client.patch(self.target_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.role.id, self.pm_role.id)