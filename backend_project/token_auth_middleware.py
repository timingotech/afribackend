import urllib.parse
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.backends import TokenBackend
from django.conf import settings


class TokenAuthMiddleware:
    """ASGI middleware that takes a `token` querystring or `Authorization` header
    and authenticates the user for WebSocket connections using Simple JWT.
    """

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return TokenAuthMiddlewareInstance(scope, self.inner)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        # Extract token from querystring `token` or from headers Authorization: Bearer <token>
        token = None
        qs = self.scope.get('query_string', b'').decode()
        params = urllib.parse.parse_qs(qs)
        if 'token' in params:
            token = params['token'][0]
        else:
            # Look in headers
            headers = dict((k.decode(), v.decode()) for k, v in self.scope.get('headers', []))
            auth = headers.get('authorization') or headers.get('Authorization')
            if auth and auth.lower().startswith('bearer '):
                token = auth.split(' ', 1)[1]

        user = AnonymousUser()
        if token:
            try:
                close_old_connections()
                tb = TokenBackend(algorithm=settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'), signing_key=settings.SECRET_KEY)
                data = tb.decode(token, verify=True)
                user_id = data.get('user_id') or data.get('user')
                if user_id:
                    User = get_user_model()
                    try:
                        user = User.objects.get(pk=user_id)
                    except Exception:
                        user = AnonymousUser()
            except Exception:
                user = AnonymousUser()

        self.scope['user'] = user
        inner = self.inner(self.scope)
        return await inner(receive, send)
