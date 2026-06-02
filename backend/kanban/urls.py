from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, KanbanColumnViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='kanban-projects')
router.register(r'columns', KanbanColumnViewSet, basename='kanban-columns')
router.register(r'tasks', TaskViewSet, basename='kanban-tasks')

urlpatterns = [
    path('', include(router.urls)),
]