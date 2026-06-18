# backend/workspace/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Import your WorkspaceViewSet alongside any project/task views
from .views import WorkspaceViewSet, ProjectViewSet, TaskViewSet 

router = DefaultRouter()
# Register the workspaces endpoint explicitly
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'projects', ProjectViewSet, basename='workspace-project')
router.register(r'tasks', TaskViewSet, basename='workspace-task')

urlpatterns = [
    path('', include(router.urls)),
]