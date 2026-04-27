from django.db import OperationalError, connection
import logging

logger = logging.getLogger(__name__)

class DBReconnectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Test the connection
            connection.ensure_connection()
        except OperationalError:
            logger.warning("Database connection lost. Attempting reconnect...")
            try:
                connection.close()
                connection.ensure_connection()
                logger.info("Database reconnected successfully.")
            except OperationalError as e:
                logger.error("Database reconnection failed: %s", e)
                # Optionally raise or return a 503 response here
        return self.get_response(request)
