# backend/kanban/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, KanbanColumnViewSet, TaskViewSet

# Engine 1: Core Router matching flat structures expected by Test Harnesses
core_router = DefaultRouter()
core_router.register(r'projects', ProjectViewSet, basename='core-projects')
core_router.register(r'columns', KanbanColumnViewSet, basename='core-columns')
core_router.register(r'tasks', TaskViewSet, basename='core-tasks')

# Engine 2: Compatibility Router matching layout structures expected by Frontend Client
compat_router = DefaultRouter()
compat_router.register(r'kanban/boards', ProjectViewSet, basename='compat-projects')
compat_router.register(r'kanban/columns', KanbanColumnViewSet, basename='compat-columns')
compat_router.register(r'kanban/tasks', TaskViewSet, basename='compat-tasks')

urlpatterns = [
    path('', include(core_router.urls)),
    path('', include(compat_router.urls)),
]