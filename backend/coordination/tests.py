# backend/coordination/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from coordination.models import Project

User = get_user_model()

class CoordinationSecurityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username="researcher_a", email="a@univ.ac.rw", password="secure_pass_1")
        self.user_b = User.objects.create_user(username="researcher_b", email="b@univ.ac.rw", password="secure_pass_2")
        
        # Instantiate Isolated Projects
        self.project_a = Project.objects.create(title="Quantum Computing Base", created_by=self.user_a)
        self.project_b = Project.objects.create(title="Bioinformatics Track", created_by=self.user_b)

    def test_tenant_isolation_boundary_enforcement(self):
        """
        Ensures researchers cannot read peer data records horizontally across tenants.
        """
        # Authenticate as user_b who has NO membership mapping in project_a
        self.client.force_authenticate(user=self.user_b)
        
        # Target project_a endpoints directly
        response = self.client.get(f'/api/projects/{self.project_a.id}/')
        
        # Assert that the multi-tenant isolation engine completely obfuscates unauthorized rows
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)