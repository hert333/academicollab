from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework import status
from authentication.models import Role

User = get_user_model()

class IdentityAuthenticationTests(APITestCase):
    def setUp(self):
        self.content_type = ContentType.objects.get_for_model(Role)
        self.perm_read = Permission.objects.create(codename='read_data', name='Read Data', content_type=self.content_type)
        
        self.role = Role.objects.create(name='Researcher')
        self.role.permissions.add(self.perm_read)
        
        self.user_password = 'ClassifiedSecurePassword2026!'
        self.user = User.objects.create_user(
            username='researcher_alpha',
            email='alpha@academicollab.edu',
            password=self.user_password,
            role=self.role
        )

    def test_jwt_token_generation_lifecycle(self):
        """Validates that valid primary user credentials generate operational token dictionaries."""
        payload = {
            'username': 'researcher_alpha',
            'password': self.user_password
        }
        response = self.client.post('/api/auth/token/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_token_denial_on_invalid_credentials(self):
        """Validates that unauthorized access requests trigger immediate 401 state blocks."""
        payload = {
            'username': 'researcher_alpha',
            'password': 'CompromisedPlaintextAttempt'
        }
        response = self.client.post('/api/auth/token/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_user_has_perm_evaluation(self):
        """Validates that the custom User model maps permission strings successfully using the RBAC link."""
        qualified_perm = f"{self.content_type.app_label}.read_data"
        self.assertTrue(self.user.has_perm(qualified_perm))
        
        # Negative test vector evaluation
        self.assertFalse(self.user.has_perm('authentication.invalid_permission_scope'))