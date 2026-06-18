# backend/authentication/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.views import RoleViewSet, UserViewSet, UserProfileView

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # 1. JWT Authentication Operations
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 2. Singular Profile Resolution
    path('user-profile/', UserProfileView.as_view(), name='dashboard_user_profile'),
    
    # 3. DRF ViewSet Mappings (Yields: users/ and roles/)
    path('', include(router.urls)),
]