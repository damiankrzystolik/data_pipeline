import uuid
import structlog
from structlog.contextvars import clear_contextvars, bind_contextvars


class RequestContextMiddleware:
    """Adds request_id to every log entry in this request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clear_contextvars()
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        bind_contextvars(
            request_id=request_id,
            path=request.path,
            method=request.method,
            user_id=str(request.user.id) if request.user.is_authenticated else 'anonymous',
        )
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response