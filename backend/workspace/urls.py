from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='workspace-project')
router.register(r'tasks', TaskViewSet, basename='workspace-task')

urlpatterns = [
    path('', include(router.urls)),
]