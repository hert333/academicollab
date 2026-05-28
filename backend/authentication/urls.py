from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import RoleViewSet, UserViewSet, UserProfileView

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Explicit Profile Endpoint matching the frontend Axios configuration
    path('auth/user-profile/', UserProfileView.as_view(), name='user_profile'),
    path('', include(router.urls)),
]