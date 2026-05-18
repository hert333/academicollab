from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import RoleViewSet, UserViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
