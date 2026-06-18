# backend/coordination/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import WorkspaceViewSet, ProjectViewSet, TaskViewSet, TaskDependencyViewSet

# Architecture Note: Import KanbanColumnViewSet from its matching application domain
from kanban.views import KanbanColumnViewSet 

router = SimpleRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'columns', KanbanColumnViewSet, basename='columns') # Resolves 404 routing failures
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'dependencies', TaskDependencyViewSet, basename='dependency')

urlpatterns = [
    path('', include(router.urls)),
]