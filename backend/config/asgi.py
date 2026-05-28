"""
ASGI config for AcademiCollab project.

It exposes the ASGI callable as a module-level variable named `application`.
"""

import os
from django.core.asgi import get_asgi_application

# Set the environment execution tracking profile target namespace configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize the foundational synchronous/asynchronous HTTP handler stack framework
django_asgi_app = get_asgi_application()

try:
    # Safely incorporate advanced routing elements if Channels is available in the ecosystem
    from channels.routing import ProtocolTypeRouter, URLRouter
    # Future integration mapping line: import your websocket routing matrix profile
    # from apps.notifications.routing import websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        # Standard HTTP payload distribution endpoint
        "http": django_asgi_app,
        
        # FIXED: Structural layout anchor for secure real-time web-socket operations
        "websocket": URLRouter(
            [] # Enforce empty array validation boundary until explicit routing nodes are linked
        ),
    })
except ImportError:
    # Fallback operation baseline profile protecting the primary container bootstrap pipeline
    application = django_asgi_app