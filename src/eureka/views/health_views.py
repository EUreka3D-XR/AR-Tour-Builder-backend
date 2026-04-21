import concurrent.futures

from django.db import connection
from django.db.utils import OperationalError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny

# Hard deadline (seconds) for the entire DB probe, including the TCP handshake.
_DB_TIMEOUT_SECONDS = 10


def _probe_db():
    """Run SELECT 1 in a worker thread and close the thread-local connection afterwards."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    finally:
        # Each thread gets its own Django DB connection; close it explicitly
        # so it is not left open after the thread returns to the pool.
        connection.close()


class HealthCheckView(APIView):
    """
    Simple health-check endpoint.

    Returns HTTP 200 when the application is running and the database
    is reachable (verified with a lightweight ``SELECT 1`` query).
    Returns HTTP 503 when the database cannot be reached or the probe
    does not complete within ``_DB_TIMEOUT_SECONDS`` seconds.

    The timeout is enforced at the Python level via a ThreadPoolExecutor,
    so it covers both the TCP connection phase and query execution.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_probe_db)
            try:
                future.result(timeout=_DB_TIMEOUT_SECONDS)
            except concurrent.futures.TimeoutError:
                return Response(
                    {"status": "error", "database": "timed out"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except OperationalError as exc:
                return Response(
                    {"status": "error", "database": str(exc)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response({"status": "ok", "database": "ok"})

