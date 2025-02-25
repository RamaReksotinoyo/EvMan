from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden

class DisableAuthForSwaggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/api/docs/'):
            request.user = None
            request.auth = None
            return None

        return None