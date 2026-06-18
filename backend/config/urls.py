# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Unified domain mapping. The frontend expects 'auth/', not 'authentication/'.
    path('api/auth/', include('authentication.urls')), 
    
    # Kanban taskboard workflows route directly to the coordination application layer
    path('api/kanban/', include('coordination.urls')),
    
    # ALIGNED: Redirect coordination layout queries straight to the workspace tracking app
    path('api/coordination/', include('workspace.urls')),
    path('api/workspace/', include('workspace.urls')),  # Kept as fallback protection
]