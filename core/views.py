from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Health"])
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Returns service health status including database connectivity."""
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False

    payload = {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }
    http_status = 200 if db_ok else 503
    return Response(payload, status=http_status)
