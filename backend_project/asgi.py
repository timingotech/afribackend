import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

# Wiring for Channels
try:
	from channels.routing import ProtocolTypeRouter, URLRouter
	# Use token-based middleware for websockets
	import apps.trips.routing as trips_routing
	from backend_project.token_auth_middleware import TokenAuthMiddleware

	application = ProtocolTypeRouter({
		"http": get_asgi_application(),
		"websocket": TokenAuthMiddleware(
			URLRouter(
				trips_routing.websocket_urlpatterns
			)
		),
	})
except Exception:
	# Fallback to standard ASGI app if channels isn't available
	application = get_asgi_application()
