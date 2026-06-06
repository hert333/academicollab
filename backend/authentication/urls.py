from django.urls import path, include
from rest_framework.routers import DefaultRouter
from authentication.views import RoleViewSet, UserViewSet, UserProfileView
from kanban_board.views import BoardViewSet, ColumnViewSet, TaskViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'users', UserViewSet, basename='user')
router.register(r'kanban/boards', BoardViewSet, basename='kanban-board')
router.register(r'kanban/columns', ColumnViewSet, basename='kanban-column')
router.register(r'kanban/tasks', TaskViewSet, basename='kanban-task')

urlpatterns = [
    # Explicit Profile Endpoint matching the frontend Axios configuration
    path('auth/user-profile/', UserProfileView.as_view(), name='user_profile'),
    path('', include(router.urls)),
]