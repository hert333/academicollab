from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProjectViewSet, TaskViewSet, TaskDependencyViewSet

router = SimpleRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'dependencies', TaskDependencyViewSet, basename='dependency')

urlpatterns = [
    path('', include(router.urls)),
]