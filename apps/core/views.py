import time
import structlog
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings

logger = structlog.get_logger(__name__)


def health_check(request):
    health = {'status': 'healthy', 'timestamp': time.time(), 'checks': {}}

    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['checks']['database'] = {
            'status': 'healthy',
            'latency_ms': round((time.time() - start) * 1000, 2),
        }
    except Exception as e:
        logger.error('health_check_database_failed', error=str(e))
        health['status'] = 'unhealthy'
        health['checks']['database'] = {'status': 'unhealthy', 'error': str(e)}

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


def readiness_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ready'})
    except Exception:
        return JsonResponse({'status': 'not ready'}, status=503)


def liveness_check(request):
    return JsonResponse({'status': 'alive'})